# Fluxo FLY
## === Infrastructure ===
main.py é o composition-root.
Ele cria as dependências Config, Logger e DataCleaner. Depois instancia o driver primário CLIAdapter e as injeta. Então chama o método start_fly().

## === Presentation ===
MetricsCollector é instanciado no construtor de CLIAdapter. WorkerPool (via WorkerPoolPort e o método abstrato run() para multithreading) também é instanciado no construtor de CLIAdapter, com MetricsCollector e WorkerPool injetado. o método run() recebe a injeção de tasks, processor, logger, e opcionalmente, on_result e post_callback. Serão utilizados pelo source na infraestrutura para tarefas multithreading. 

start_fly() é chamado e executa três serviços, em sequência: os métodos _company_service(), _nsd_service() e _statement_service().

## O método _company_service() 
Primeiro instancia Mapper, Repository e Scraper, com a seguintes características. 
Mapper: CompanyMapper, que mescla o CompanyListingDTO com o CompanyDetailDTO para retornar o CompanyDataRawDTO. 
Repository: SqlAlchemyCompanyRepository é construído com base em duas classes, uma base genérica e uma base específica. 
A base genérica vem de SqlAlchemyRepositoryBasePort, com os métodos abstratos como save_all(), get_all(), has_item(), get_by_id() e get_all_primary_keys(). As implementações concretas comuns a todos os repositórios são realizadas em SqlAlchemyRepositoryBase, que acrescenta o método abstrado para buscar o model (get_model_class(). 
A base específica para Company tem os métodos abstratos específicos em SqlAlchemyCompanyRepositoryPort e a implantação dos métodos concretos em SqlAlchemyCompanyRepository, como o get_model_class(). 
Scraper: CompanyDataScraper, que implementa o contrato CompanyDataScraperPort, derivado de BaseScraperPort (comum a todos os sources) para CompanyDataRawDTO (com o método fetch_all()). 
A construção de CompanyDataScraper recebe as dependências criadas CompanyMapper e injetadas WorkerPoolExecutor e MetricsCollector, e também segue o princípio de substituição de Liskov. Além disso, o construtor do CompanyDataScraper cria instâncias de EntryCleaner, DetailFetcher (e seu método fetch_detail()) e session, que contém o scraper, e que vão ser injetados na instanciação de CompanyDataDetailProcessor. O CompanyDataDetailProcessor contém o método process_entry, que vai realizar a implantação concreta do código. 
Então o método _company_service() instancia o serviço CompanyDataService com a injeção do Repository e do Scraper, e chama o método sync_companies()
## === Application ===
O construtor do serviço CompanyDataService recebe repository e scraper e instancia o SyncCompanyDataUseCase com a injeção das dependências recebidas. 

O método sync_companies() do CompanyDataService chama o método synchronize_companies() do SyncCompanyDataUseCase. 

O método synchronize_companies() de SyncCompanyDataUseCase inicia o pipeline completo de sincronização: 
Primeiro coleta os códigos primários existentes via get_all_primary_keys() do repository, 
Depois chama fetch_all() do scraper passando os códigos a serem ignorados e o método _save_batch() instanciado aqui. Esse método _save_batch() é responsável por persistir os resultados do método fetch_all() da source para o repositório através do método save_all(). 

Após a execução, o método synchronize_companies() de SyncCompanyDataUseCase calcula o tempo decorrido e os bytes transferidos, e retorna um SyncCompanyDataResultDTO com métricas agregadas da execução a partir de um ExecutionResultDTO recebido. 

O ExecutionResultDTO contém uma lista de items (companies, recebida de fetch_all() através de detail_exec.items) e métricas na forma de MetricsDTO (elapsed time, network_bytes, processing_bytes e failures). 

E o SyncCompanyDataResultDTO contém processed_count, skipped_count, bytes_downloaded, elapsed_time, warnings. 

Esse resultado de métricas não é utilizado. 

## === Infrastructure ===
O método fetch_all() do CompanyDataScraper é implementado através de uma porta CompanyDataScraperPort via BaseScraperPort, e pela implantação concreta no scraper injetado. O método concreto fetch_all() do CompanyDataScraper executa duas etapas: _fetch_companies_list() e _fetch_companies_details(), com a injeção de _save_batch() em ambos. 

### _fetch_companies_list()
O método concreto fetch_all() do CompanyDataScraper primeiro chama _fetch_companies_list() também do CompanyDataScraper, que delega a execução em multithreading ao método run() do WorkerPool (instanciado no CLIAdapter), com a injeção no run() das tasks e do método processor() e do método handle_batch(), que neste caso é nulo. Cada vez que o método processor() for chamado pelo run(), vai chamar o método _fetch_page() de CompanyDataScraper, que é onde a implementação é executada. Os resultados são acumulados e salvos periodicamente por meio do SaveStrategy instanciado. O método _fetch_page() recupera e processa o response de um url. 
O SaveStrategy apresenta  os métodos handle(), que verifica os critérios para chamar o flush(). O flush() chama o método injetado para persistir no repositório. 

### _fetch_companies_details()
O método concreto fetch_all() do CompanyDataScraper depois chama _fetch_companies_details() do CompanyDataScraper, que delega a execução em multithreading ao método run() do WorkerPool (instanciado no CLIAdapter), com a injeção no run() das tasks, do novo método processor() e do método handle_batch() do SaveStrategy. Os resultados são acumulados e salvos periodicamente por meio dos métodos handle() e flush() do SaveStrategy. O processor vai chamar o método process_entry() do CompanyDataDetailProcessor que foi instanciado na construção do CompanyDataScraper. O process_entry() chama o método fetch_detatil do DetailFetcher injetado e o método merge_details() do CompanyDataMerger. 

Durante a execução de _fetch_companies_details(), o método run() do WorkerPool recebe as tasks, o processor() e o on_result() (que aponta para o método handle_batch() do SaveStrategy). Ele utiliza o recurso de ThreadPoolExecutor para chamar várias instâncias simultâneas do método worker. 

Cada worker processa uma task e retorna um CompanyDataRawDTO (ou None). Esses resultados são acumulados na lista results definida dentro do escopo de WorkerPool.run(). A cada retorno do processor(), o resultado também é encaminhado para o método on_result(), que por sua vez chama o handle() do SaveStrategy, responsável por controlar o threshold de persistência e disparar flush() quando necessário.

Ao final da execução paralela, a fila de tarefas é esvaziada, os workers são finalizados, e o método finalize() do SaveStrategy é chamado para garantir o flush final dos dados que ainda estiverem no buffer.

O resultado final é um ExecutionResultDTO contendo os dados e as métricas do processamento.

Este ExecutionResultDTO é finalizado em synchronize_companies(), que retorna um SyncCompanyDataResultDTO com incorporação de métricas do processamento. Essas métricas são devolvidas pelo SyncCompanyDataUseCase para o CompanyDataService, que devolve para o CLIAdapter, que nem usa. 

## O método _nsd_service()
Instancia o repositório e o scraper. 
Repository: SqlAlchemyCompanyRepository, que implementa os métodos do contrato CompanyRepositoryPort, herdados de BaseRepositoryPort (com os métodos save_all(), get_all(), has_item(), get_by_id() e get_all_primary_keys()), e também do BaseRepository, via BaseRepositoryPort. O módulo de construção do BaseRepository garante a implementação concreta dos repositórios no banco de dados. A implementação respeita o princípio de substituição de Liskov.
Scraper: NsdScraper, que implementa o contrato NSDSourcePort, derivado de BaseScraperPort (com o método fetch_all()). Sua construção recebe as dependências criadas FetchUtils e injetadas WorkerPoolExecutor e MetricsCollector, e também segue o princípio de substituição de Liskov. 

Então o método _nsd_service() instancia o serviço NsdService com a injeção do Repository e do Scraper, e chama o método sync_nsd()

## === Application ===
O construtor do serviço NsdService recebe repository e scraper e instancia o SyncNSDUseCase com a injeção das dependências recebidas. 

O método sync_nsd() do NsdService chama o método synchronize_nsd() do SyncNSDUseCase. 

O método synchronize_nsd() inicia o pipeline completo de sincronização: 
Primeiro coleta os códigos primários existentes via repository, 
Depois chama scraper.fetch_all() passando os códigos a serem ignorados e o método _save_batch() instanciado aqui. Esse método _save_batch() é responsável por persistir os resultados do método fetch_all() da source para método save_all() do repositório. 

## === Infrastructure ===
O método fetch_all() do NsdScraper é implementado através de uma porta NSDSourcePort via BaseScraperPort, e pela implantação concreta no scraper injetado e executa uma etapa através do método processor(). Chama o método run() do WorkerPoolExecutor e injeta tasks, processor, que é o método processor() e on_result, que é o método handle_batch() que vai chamar o StrategySave.handle(). O processor 

