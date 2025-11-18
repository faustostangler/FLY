import argparse
from utils.base_processor import BaseProcessor
from utils.company_data_processor import CompanyDataProcessor
from utils.corporate_events_processor import EventsStatementsProcessor
from utils.intel_processor import IntelProcessor
from utils.nsd_processor import NsdProcessor
from utils.statements_processor import StatementsProcessor


def run(args):
    """Executa os módulos do FLY conforme as flags passadas via linha de comando.

    Se nenhuma flag for passada ou --all for usada, todos os módulos são executados em sequência.
    """
    # Se --all for usado, ou nenhuma flag for passada, executa tudo
    all_flags = [args.company, args.nsd, args.statements, args.standardize, args.events]
    if args.all or not any(all_flags):
        print("[INFO] Nenhuma flag ou --all usado. Executando todos os módulos...")
        args.company = args.nsd = args.statements = args.standardize = args.events = True

    try:
        if args.company:
            print("[PROCESS] CompanyDataProcessor iniciado...")
            CompanyDataProcessor().main(thread=True)

        if args.nsd:
            print("[PROCESS] NsdProcessor iniciado...")
            NsdProcessor().main(thread=True)

        if args.statements:
            print("[PROCESS] StatementsProcessor iniciado...")
            StatementsProcessor().main(thread=False)

        if args.standardize:
            print("[PROCESS] IntelProcessor (standardization) iniciado...")
            IntelProcessor().main(thread=False)

        if args.events:
            print("[PROCESS] EventsStatementsProcessor iniciado...")
            EventsStatementsProcessor().main(thread=False)

        print("[DONE] Execução finalizada com sucesso.")

    except Exception as e:
        print(f"[ERROR] Ocorreu um erro: {e}")

def main():
    """Parser de linha de comando para o app FLY."""
    try:
        parser = argparse.ArgumentParser(description="FLY: Financial Ledger Yearly - CLI Options")

        parser.add_argument('--all', action='store_true', help="Executa todos os processadores em sequência")

        parser.add_argument('--company', action='store_true', help="Atualiza dados de empresas")
        parser.add_argument('--nsd', action='store_true', help="Atualiza dados NSD")
        parser.add_argument('--statements', action='store_true', help="Baixa demonstrações financeiras")
        parser.add_argument('--standardize', action='store_true', help="Padroniza demonstrações")
        parser.add_argument('--events', action='store_true', help="Baixa eventos corporativos")

        args = parser.parse_args()
        run(args)
    except Exception as e:
        BaseProcessor().log_error(e)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        BaseProcessor().log_error(e)
    print("done")

# if __name__ == "__main__":
#     try:
#         base = BaseProcessor()

#         # Ask the user if they want to get company information
#         run_company_data_processor = "N"
#         prompt = "Want to update company information? (YES/NO): "
#         run_company_data_processor = base.timed_input(prompt)
#         if run_company_data_processor.strip().upper().startswith("Y"):
#             company_data_processor = CompanyDataProcessor()
#             company_data_processor.main(thread=True)

#         # Ask the user if they want to get nsd information
#         run_nsd_processor = "N"
#         prompt = "Want to update nsd information? (YES/NO): "
#         run_nsd_processor = base.timed_input(prompt)
#         if run_nsd_processor.strip().upper().startswith("Y"):
#             nsd_processor = NsdProcessor()
#             nsd_processor.main(thread=True)

#         # Ask the user if they want to get finantial statements
#         run_statements_processor = "N"
#         prompt = "Want to update statements information? (YES/NO): "
#         run_statements_processor = base.timed_input(prompt)
#         if run_statements_processor.strip().upper().startswith("Y"):
#             statements_processor = StatementsProcessor()
#             statements_processor.main(thread=True)

#         # Ask the user if they want to sstandardize the statements
#         run_intel_processor = "N"
#         prompt = "Want to standardize statements information? (YES/NO): "
#         run_intel_processor = base.timed_input(prompt)
#         if run_intel_processor.strip().upper().startswith("Y"):
#             intel_processor = IntelProcessor()
#             intel_processor.main(thread=False)

#         # Ask the user if they want to get corporate events from b3
#         run_corporate_events_processor = "Y"
#         prompt = "Want to update corporate events? (YES/NO): "
#         run_corporate_events_processor = base.timed_input(prompt)
#         if run_corporate_events_processor.strip().upper().startswith("Y"):
#             events_states_processor = EventsStatementsProcessor()
#             events_states_processor.main(thread=False)

#             # corporate_events_merger = CorporateEventsMerger()
#             # corporate_events_merger.main(thread=False)

#         # # Ask the user if they want to get finantial historical market data direct form b3 source
#         # stock_processor = StockProcessor()
#         # run_stock_processor = 'Y'
#         # prompt = 'Want to update stock historical data? (YES/NO): '
#         # # run_stock_processor = stock_processor.timed_input(prompt)
#         # if run_stock_processor.strip().upper().startswith('Y'):
#         #     stock_processor.main(thread=True)
#         # stock_processor.close_driver()

#     except Exception as e:
#         base.log_error(e)
#         pass

    # print("done")
