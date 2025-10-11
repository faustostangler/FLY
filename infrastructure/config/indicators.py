from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, List, Tuple

# 
ENDPOINT = {
    "bcb": 
    "http://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/"
    "dados?formato=json&dataInicial={dataInicial}&dataFinal={dataFinal}"

    }

SOURCE = {
    "bcb": [
        # 1. Economic Activity
        # 1. 1. PIB e IBC
        # Economic activity and price indicators - Real sector - National accounts
        ('4380', 'GDP monthly - current prices (BCB-Depec)', 'Monthly'), # BCB-Depec - GDP monthly - current prices (R$ million)
        ('4385', 'GDP monthly in dollar (BCB-Depec)', 'Monthly'), # BCB-Depec - GDP monthly - in US$ million
        # Economic activity and price indicators - Real sector - National accounts
        ('24364', 'IBC-Br - seasonally adjusted (BCB-Depec)', 'Monthly'), # BCB-Depec - Central Bank Economic Activity Index (IBC-Br) - seasonally adjusted
        ('29602', 'IBC-Br - Agriculture seasonally adjusted (BCB-Depec)', 'Monthly'), # BCB-Depec - Central Bank Economic Activity Index (IBC-Br) Agriculture - seasonally adjusted
        ('29604', 'IBC-Br Industry - seasonally adjusted (BCB-Depec)', 'Monthly'), # BCB-Depec - Central Bank Economic Activity Index (IBC-Br) Industry - seasonally adjusted
        ('29606', 'IBC-Br Services - seasonally adjusted (BCB-Depec)', 'Monthly'), # BCB-Depec - Central Bank Economic Activity Index (IBC-Br) Services - seasonally adjusted
        ('29608', 'IBC-Br Nonfarm - seasonally adjusted (BCB-Depec)', 'Monthly'), # BCB-Depec - Central Bank Economic Activity Index (IBC-Br) Nonfarm - seasonally adjusted
        ('29610', 'IBC-Br Taxes - seasonally adjusted (BCB-Depec)', 'Monthly'), # BCB-Depec - Central Bank Economic Activity Index (IBC-Br) Taxes - seasonally adjusted

        # 1. 2. Economic Activity
        # Economic activity and price indicators-Real sector-National accounts-Quarterly GDP-seasonally adjusted data # SCN Sistema de Contas Nacionais
        ('22105', 'Crop and livestock (total) SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Crop and livestock (total)
        ('22106', 'Industry (total) SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Industry (total)
        ('22107', 'Services (total) SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Services (total)
        ('22108', 'Value added at basic prices SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Value added at basic prices
        ('22109', 'GDP at market prices SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - GDP at market prices
        ('22110', 'Private consumption SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Private consumption
        ('22111', 'Government consumption SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Government consumption
        ('22113', 'Investiment SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Investiment
        ('22114', 'Exports SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Exports
        ('22115', 'Imports SCN-2010 (IBGE)', 'Quarterly'), # IBGE - Quarterly GDP - seasonally adjusted data - Imports
        # Economic activity and price indicators-Real sector-Services and Trade-Sales volume index of the retail sector-total/segments
        ('28473', 'Sales volume Total - Brazil - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Sales volume index in the retail sector - Total - Brazil - Seasonally Adjusted
        ('28474', 'Sales volume Fuel and lubricants - Brazil - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Sales volume index in the retail sector - Fuel and lubricants - Brazil - Seasonally Adjusted
        ('28475', 'Sales volume Hypermarkets, supermarkets, food, beverages and tobacco - Brazil - SeasonalllyAdjusted (IBGE)', 'Monthly'), # IBGE - Sales volume index in the retail sector - Hypermarkets, supermarkets, food, beverages and tobacco - Brazil - SeasonalllyAdjusted
        ('28476', 'Sales volume Hypermarkets and supermarkets - Brazil - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Sales volume index in the retail sector - Hypermarkets and supermarkets - Brazil - Seasonally Adjusted
        ('28477', 'Sales volume Textiles, Clothing and Footwear - Brazil - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Sales volume index in the retail sector - Textiles, Clothing and Footwear - Brazil - Seasonally Adjusted
        ('28478', 'Sales volume Furniture and white goods - Brazil - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Sales volume index in the retail sector - Furniture and white goods - Brazil - Seasonally Adjusted
        ('28479', 'Sales volume Vehicles and motorcycles, spare parts - Brazil - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Sales volume index in the retail sector - Vehicles and motorcycles, spare parts - Brazil - Seasonally Adjusted
        ('28480', 'Sales volume Pharmac., medical, orthop. and perfumery articles - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Pharmac., medical, orthop. and perfumery articles - Seasonally Adjusted
        ('28481', 'Sales volume Books, newspaper, magazines, - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Books, newspaper, magazines, - Seasonally Adjusted
        ('28482', 'Sales volume Office, comp./comunic. equip. - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Office, comp./comunic. equip. - Seasonally Adjusted
        ('28483', 'Sales volume Other art. of personal use - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Other art. of personal use - Seasonally Adjusted
        ('28484', 'Sales volume Building materials - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Building materials - Seasonally Adjusted
        ('28485', 'Sales volume Broad trade sector - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Broad trade sector - Seasonally Adjusted

        # 1. 3. IPCA
        # Economic activity and price indicators-Price indicators-Consumer price indices-IPCA-IPCA and its main components
        ('433', 'IPCA - Broad National Consumer Price Index (IPCA) (IBGE)', 'Monthly'), # IBGE - Broad National Consumer Price Index (IPCA)
        ('1635', 'IPCA - Food and beverages (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Food and beverages
        ('1636', 'IPCA - Housing (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Housing
        ('1637', 'IPCA - Domestic goods (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Domestic goods
        ('1638', 'IPCA - Clothing (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Clothing
        ('1639', 'IPCA - Transport (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Transport
        ('1640', 'IPCA - Communication (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Communication
        ('1641', 'IPCA - Health and personal care (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Health and personal care
        ('1642', 'IPCA - Personal expenditures (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Personal expenditures
        ('1643', 'IPCA - Education (IBGE)', 'Monthly'), # IBGE - Broad national consumer price index (IPCA) - Education
        # Economic activity and price indicators-Price indicators-Consumer price indices-IPCA-Core inflation measures and diffusion index
        ('4466', 'IPCA - Smoothed trimmed mean Core IPCA (BCB-Depec)', 'Monthly'), # BCB-Depec - Broad national consumer price index - Smoothed trimmed mean Core IPCA
        ('21379', 'IPCA - Diffusion index Highly Important (BCB-Depec)', 'Monthly'), # BCB-Depec - Broad national consumer price index (IPCA) - Diffusion index # núcleos oficiais do BCB para detectar a tendência central da inflação. ## muito importante
        ('16122', 'IPCA - Double Weighted Core IPCA (BCB-Depec)', 'Monthly'), # BCB-Depec - Broad national consumer price index - Double Weighted Core IPCA # núcleos oficiais do BCB para detectar a tendência central da inflação.
        ('16121', 'IPCA - EX1 Core IPCA (BCB-Depec)', 'Monthly'), # BCB-Depec - Broad national consumer price index - EX1 Core IPCA # refletem inflação persistente e sensível à política monetária.
        ('28751', 'IPCA - EXFE Core / IPCA (BCB-Depec)', 'Monthly'), # BCB-Depec - Broad National Consumer Price Index - Ex-Food and Energy (EXFE) core # refletem inflação persistente e sensível à política monetária.

        # 1. 4. Desemprego
        # Economic activity and price indicators-Labor market-Open unemployment-Open unemployment rate
        ('24369', 'Unemployment rate - PNADC (IBGE)', 'Monthly'), # IBGE - Unemployment rate - PNADC
        ('28562', 'Unemployment rate - PNADC - North (IBGE)', 'Quarterly'), # IBGE - Unemployment rate - PNADC - North
        ('28563', 'Unemployment rate - PNADC - Central-West (IBGE)', 'Quarterly'), # IBGE - Unemployment rate - PNADC - Central-West
        ('28564', 'Unemployment rate - PNADC - Northeast (IBGE)', 'Quarterly'), # IBGE - Unemployment rate - PNADC - Northeast
        ('28565', 'Unemployment rate - PNADC - Southeast (IBGE)', 'Quarterly'), # IBGE - Unemployment rate - PNADC - Southeast
        ('28566', 'Unemployment rate - PNADC - South (IBGE)', 'Quarterly'), # IBGE - Unemployment rate - PNADC - South

        # 1. 5. Produção Industrial
        # Economic activity and price indicators-Real sector-Industrial production indicators-Industrial output indicators (2012 = 100)
        ('28503', 'Physical Production - General (2022=100) Seasoally Adjusted (IBGE)', 'Monthly'), # IBGE - General (2022=100) Seasoally Adjusted
        ('28504', 'Physical Production - Mineral extraction - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Physical Production - Mineral extraction - Seasonally Adjusted
        ('28505', 'Physical Production - Manufacturing industry - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Physical Production - Manufacturing industry - Seasonally Adjusted
        ('28506', 'Physical Production - Capital goods - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Physical Production - Capital goods - Seasonally Adjusted
        ('28507', 'Physical Production - Intermediate goods - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Physical Production - Intermediate goods - Seasonally Adjusted
        ('28508', 'Physical Production - Consumer goods - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Physical Production - Consumer goods - Seasonally Adjusted
        ('28509', 'Physical Production - Durable goods - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Physical Production - Durable goods - Seasonally Adjusted
        ('28510', 'Physical Production - Semidurable and nondurable goods - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Physical Production - Semidurable and nondurable goods - Seasonally Adjusted
        ('28511', 'Physical Production - Production of construction inputs - Seasonally Adjusted (IBGE)', 'Monthly'), # IBGE - Physical Production - Production of construction inputs - Seasonally Adjusted
        # Economic activity and price indicators-Real sector-Industrial production indicators-Installed capacity utilization
        ('28561', 'Physical Production Capacity utilization - manufacturing industry (FGV) - Seasonally Adjusted (FGV)', 'Monthly'), # FGV - Capacity utilization – manufacturing industry (FGV) - Seasonally Adjusted

        # 2. Taxas e ìndices
        # 2. 1. Índices
        # Capital and financial markets-Financial market indicators-Interest rate
        ('11', 'Taxa - Selic (BCB-Demab)', 'Daily'), # BCB-Demab - Interest rate - Selic
        ('432', 'Taxa - Selic target (Copom)', 'Daily'), # Copom - Interest rate - Selic target
        ('12', 'Taxa - CDI (Cetip)', 'Daily'), # Cetip - Interest rate - CDI
        ('226', 'Taxa - Referential rate (TR) (BCB-Demab)', 'Daily'), # BCB-Demab - Referential rate (TR)
        ('256', 'Taxa - Long term interest rate (TJLP) (BCB-Demab)', 'Monthly'), # BCB-Demab - Long term interest rate (TJLP)
        ('29565', 'Taxa - Pm rate (BCB-Demab)', 'Monthly'), # BCB-Demab - Pm - 5-year fixed interest rate, in accordance with Law No. 13,483/2017
        ('29566', 'Taxa - PMm rate (BCB-Demab)', 'Monthly'), # BCB-Demab - PMm - 3-year fixed interest rate of the Financing Program for Micro, Small and Medium Enterprises, in accordance with Law No. 13,483/2017
        # Economic activity and price indicators-Labor market-Minimum wage, real average earnings and overall earnings
        ('1619', 'Taxa - Minimum wage (MTb)', 'Monthly'), # MTb - Minimum wage
        ('24381', 'Taxa - Ganho Médio - Real effective average earnings of employed people - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real effective average earnings of employed people - Continuous PNAD
        ('28544', 'Taxa - Ganho Total - Real effective overall earnings (IBGE)', 'Monthly'), # IBGE - Real effective overall earnings
        ('29023', 'Taxa - Renda Familiar - Households disposable income (BCB)', 'Monthly'), # BCB - Households gross disposable national income (3-months moving average)
        ('24382', 'Taxa - Renda - Real habitually average earnings of employed people - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real habitually average earnings of employed people - Continuous PNAD
        ('24383', 'Taxa - Renda - Real habitually average earnings of employed people - Registered - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real habitually average earnings of employed people - Registered - Continuous PNAD
        ('24384', 'Taxa - Renda - Real habitually average earnings of employed people - Nonregistered - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real habitually average earnings of employed people - Nonregistered - Continuous PNAD
        ('24385', 'Taxa - Renda - Real habitually average earnings of employed people - Private sector - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real habitually average earnings of employed people - Private sector - Continuous PNAD
        ('24386', 'Taxa - Renda - Real habitually average earnings of employed people - Public sector - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real habitually average earnings of employed people - Public sector - Continuous PNAD
        ('24387', 'Taxa - Renda - Real habitually average earnings of employed people - Self-employed - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real habitually average earnings of employed people - Self-employed - Continuous PNAD
        ('24388', 'Taxa - Renda - Real habitually average earnings of employed people - Employer - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real habitually average earnings of employed people - Employer - Continuous PNAD
        ('24399', 'Taxa - Renda - Real habitually average earnings of employed people - Private and Public sector - Continuous PNAD (IBGE)', 'Monthly'), # IBGE - Real habitually average earnings of employed people - Private and Public sector - Continuous PNAD

        # Credit statistics-Average cost of outstanding loans (ICC)-Average cost of outstanding loans
        ('25351', 'Custo do Crédito ICC - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Average cost of outstanding loans - ICC - Total
        ('25352', 'Custo do Crédito ICC - Non-financial corporations - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Average cost of outstanding loans - ICC - Non-financial corporations - Total
        ('25353', 'Custo do Crédito ICC - Individuals - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Average cost of outstanding loans - ICC - Individuals - Total

        # 2. 2. Crédito
        # Credit statistics-Credit outstanding-Credit as percentage of GDP-Credit outstanding as percentage of GDP
        ('20622', 'Credit outstanding / GDP (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Credit operations outstanding - % of GDP
        ('20623', 'Credit outstanding - Non-financial corporations / GDP (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Credit operations outstanding - Non-financial corporations - % of GDP
        ('20624', 'Credit outstanding - Households / GDP (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Credit operations outstanding - Households - % of GDP

        # 2. 3. Risco de Crédito e Inadimplência
        # Credit statistics-Delinquent loans-90 days past due loans
        ('21003', 'Credit outstanding - Arrears - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Percent of arrears from 15 to 90 days of credit operations outstanding - Total
        ('21004', 'Credit outstanding - Arrears - Non-financial corporations - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Percent of arrears from 15 to 90 days of credit operations outstanding - Non-financial corporations - Total
        ('21005', 'Credit outstanding - Arrears - Individual persons - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Percent of arrears from 15 to 90 days of credit operations outstanding - Households - Total
        ('21082', 'Credit outstanding - 90 days past due loans - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Percent of 90 days past due loans of credit operations outstanding - Total
        ('21083', 'Credit outstanding - 90 days past due loans - Non-financial corporations - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Percent of 90 days past due loans of credit operations outstanding - Non-financial corporations - Total
        ('21084', 'Credit outstanding - 90 days past due loans - Individual persons - Total (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Percent of 90 days past due loans of credit operations outstanding - Households - Total
        # Credit statistics-Quarterly credit conditions survey-Credit demand indicators
        ('21381', 'Credit Conditions - QSCC - Corporate - Observed demand (BCB-Depep)', 'Quarterly'), # BCB-Depep - Quartely Survey on Credit Condition - Corporate - Observed demand
        ('21383', 'Credit Conditions - QSCC - MSME - Observed demand (BCB-Depep)', 'Quarterly'), # BCB-Depep - Quartely Survey on Credit Condition - Micro, small and medium enterprises - Observed demand
        ('21385', 'Credit Conditions - QSCC - Consumption - Observed demand (BCB-Depep)', 'Quarterly'), # BCB-Depep - Quartely Survey on Credit Condition - Consumer Credit - Observed demand
        ('21387', 'Credit Conditions - QSCC - Mortgage - Observed demand (BCB-Depep)', 'Quarterly'), # BCB-Depep - Quartely Survey on Credit Condition - Mortgage - Observed demand
        # Credit statistics-Quarterly credit conditions survey-Credit supply indicators
        ('21389', 'Credit Conditions - QSCC - Corporate - Observed supply (BCB-Depep)', 'Quarterly'), # BCB-Depep - Quartely Survey on Credit Condition - Corporate - Observed supply
        ('21391', 'Credit Conditions - QSCC - MSME - Observed supply (BCB-Depep)', 'Quarterly'), # BCB-Depep - Quartely Survey on Credit Condition - Micro, small and medium enterprises - Observed supply
        ('21393', 'Credit Conditions - QSCC - Consumption - Observed supply (BCB-Depep)', 'Quarterly'), # BCB-Depep - Quartely Survey on Credit Condition - Consumer Credit - Observed supply
        ('21395', 'Credit Conditions - QSCC - Mortgage - Observed supply (BCB-Depep)', 'Quarterly'), # BCB-Depep - Quartely Survey on Credit Condition - Mortgage - Observed supply

        # 2. 4. Agregados Monetários
        # Monetary statistics-Monetary aggregates-Money supply
        ('27841', 'Agregado Monetário - M1 (end-of-period balance) -New - seasonally adjusted (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Money supply - M1 (end-of-period balance) - New - seasonally adjusted
        ('27842', 'Agregado Monetário - M2 (end-of-period balance) - New - seasonally adjusted (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - M2 (end-of-period balance) - New - seasonally adjusted
        # M1
        ('27791', 'Agregado Monetário - M1 (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Money supply - M1 (end-of-period balance) - New
        ('27805', 'Agregado Monetário - M1 - Time deposits (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - Time deposits (end-of-period balance) - New
        ('27806', 'Agregado Monetário - M1 - Financial bonds (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - Financial bonds (end-of-period balance) - New
        ('27807', 'Agregado Monetário - M1 - Exchange bills (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - Exchange bills (end-of-period balance) - New
        ('27808', 'Agregado Monetário - M1 - Others private securities - (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - Others private securities - (end-of-period balance) - New
        ('27809', 'Agregado Monetário - M1 - Private securities held by the public (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply- Private securities held by the public (end-of-period balance) - New
        # M2
        ('27810', 'Agregado Monetário - M2 (end-of-periodo balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - M2 (end-of-periodo balance) - New
        ('27811', 'Agregado Monetário - M2 - Money market funds quotas (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - Money market funds quotass (end-of-period balance) - New
        ('27812', 'Agregado Monetário - M2 - Operations committed with private securities (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - Operations committed with private securities (end-of-period balance) - New
        # M3
        ('27813', 'Agregado Monetário - M3 (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - M3 (end-of-period balance) - New
        ('27814', 'Agregado Monetário - M3 - Federal securities held by the public (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - Federal securities held by the public (end-of-period balance) - New
        # M4
        ('27815', 'Agregado MonetárioM4 (end-of-period balance) - New (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Broad money supply - M4 (end-of-period balance) - New


        # 3. Dívida
        # Fiscal statistics-Net public debt and general government debt-Percent of GDP (% GDP)-Fiscal net debt
        ('10831', 'Fiscal - Dívida - Fiscal net debt - 10831 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Fiscal net debt (% GDP)
        # Fiscal statistics-Public sector borrowing requirements without exchange devaluation-Percent of GDP-Current monthly flows (% GDP)-Total primary result
        ('5364', 'Consolidated public sector - 5364 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - Consolidated public sector
        # Governments
        ('5355', 'Federal Government - 5355 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - Federal Government
        ('5358', 'State governments - 5358 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - State governments
        ('5359', 'Municipal governments - 5359 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - Municipal governments
        # Government Enterprises
        ('5361', 'Federal government enterprises - 5361 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - Federal government enterprises
        ('5362', 'State government enterprises - 5362 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - State government enterprises
        ('5363', 'Municipal government enterprises - 5363 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - Municipal government enterprises
        # Federal Institutions
        ('5356', 'Banco Central - 5356 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - Banco Central
        ('7864', 'National Social Security Institute - 7864 (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - PBSR (%GDP) - Current monthly flows - Primary result - Total - National Social Security Institute

        # 4 External sector statistics-Balance of Payments-BPM6-Balance of payments indicators-Current account accumulated in 12 months
        # 1. Current Account
        # 1. 1. Current Account
        ('22701', 'External Sector - 1.1. Current account - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Current account - monthly - net
        ('22702', 'External Sector - 1.1. Current account - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Current account - monthly - credit
        ('22703', 'External Sector - 1.1. Current account - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Current account - monthly - debit
        # 1. 2. Balance of Payments
        ('22707', 'External Sector - 1.2. Balance on goods - Balance of Payments - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Balance on goods - Balance of Payments - monthly - net
        ('22708', 'External Sector - 1.2. Exports - Balance of Payments - monthly (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Exports - Balance of Payments - monthly
        ('22709', 'External Sector - 1.2. Imports - Balance of Payments - monthly (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Imports - Balance of Payments - monthly

        # 2. Goods - goods and services
        ('22704', 'External Sector - 2. Balance on goods and services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Balance on goods and services - monthly - net
        ('22705', 'External Sector - 2. Balance on goods and services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Balance on goods and services - monthly - credit
        ('22706', 'External Sector - 2. Balance on goods and services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Balance on goods and services - monthly - debit
        # 2. 1. general merchandise
        ('22710', 'External Sector - 2.1. Balance on goods - general merchandise - Balance of Payments - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Balance on goods - general merchandise - Balance of Payments - monthly - net
        ('22711', 'External Sector - 2.1. Exports - general merchandise - Balance of Payments - monthly (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Exports - general merchandise - Balance of Payments - monthly
        ('22712', 'External Sector - 2.1. Imports - general merchandise - Balance of Payments - monthly (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Imports - general merchandise - Balance of Payments - monthly
        # 2. 2. under merchanting
        ('22713', 'External Sector - 2.2. Balance on goods - exports under merchanting - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Balance on goods - exports under merchanting - monthly - net
        ('22714', 'External Sector - 2.2. Exported goods under merchanting - positive exports - monthly (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Exported goods under merchanting - positive exports - monthly
        ('22715', 'External Sector - 2.2. Imported goods under merchanting - negative exports - monthly (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Imported goods under merchanting - negative exports - monthly
        # 2. 3. non-monetary gold
        ('22716', 'External Sector - 2.3. Balance on goods - non-monetary gold - Balance of Payments - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Balance on goods - non-monetary gold - Balance of Payments - monthly - net
        ('22717', 'External Sector - 2.3. Exports - non-monetary gold - Balance of Payments - monthly (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Exports - non-monetary gold - Balance of Payments - monthly
        ('22718', 'External Sector - 2.3. Imports - non-monetary gold - Balance of Payments - monthly (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Imports - non-monetary gold - Balance of Payments - monthly

        ('24419', 'External Sector - 3. Balance of Payments - Current account accumulated in 12 months - monthly (BCB-DSTAT)', 'Monthly'), # BCB-DSTAT - Current account accumulated in 12 months - monthly
        # 3. Services
        # 3. 1. Manufacturing services on physical inputs owned by others
        ('22722', 'External Sector - 3.1. Manufacturing services on physical inputs owned by others - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Manufacturing services on physical inputs owned by others - monthly - net
        ('22723', 'External Sector - 3.1. Manufacturing services on physical inputs owned by others - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Manufacturing services on physical inputs owned by others - monthly - credit
        ('22724', 'External Sector - 3.1. Manufacturing services on physical inputs owned by others - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Manufacturing services on physical inputs owned by others - monthly - debit
        # 3. 2. Maintenance and repair services
        ('22725', 'External Sector - 3.2. Maintenance and repair services n.i.e. - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Maintenance and repair services n.i.e. - monthly - net
        ('22726', 'External Sector - 3.2. Maintenance and repair services n.i.e. - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Maintenance and repair services n.i.e. - monthly - credit
        ('22727', 'External Sector - 3.2. Maintenance and repair services n.i.e. - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Maintenance and repair services n.i.e. - monthly - debit
        # 3. 3. 1. Transport - Passenger
        ('22731', 'External Sector - 3.3.1. Transport - Passenger - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Transport - Passenger - monthly - net
        ('22732', 'External Sector - 3.3.1. Transport - Passenger - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Transport - Passenger - monthly - credit
        ('22733', 'External Sector - 3.3.1. Transport - Passenger - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Transport - Passenger - monthly - debit
        # 3. 3. 2. Transport - Freight
        ('22734', 'External Sector - 3.3.2. Transport - Freight - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Transport - Freight - monthly - net
        ('22735', 'External Sector - 3.3.2. Transport - Freight - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Transport - Freight - monthly - credit
        ('22736', 'External Sector - 3.3.2. Transport - Freight - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Transport - Freight - monthly - debit
        # 3. 3. 3. Other transport services
        ('22737', 'External Sector - 3.3.3. Other transport services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Other transport services - monthly - net
        ('22738', 'External Sector - 3.3.3. Other transport services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Other transport services - monthly - credit
        ('22739', 'External Sector - 3.3.3. Other transport services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Other transport services - monthly - debit
        # 3. 4. Travel
        ('22740', 'External Sector - 3.4. Travel - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - monthly - net
        ('22741', 'External Sector - 3.4. Travel - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - monthly - credit
        ('22742', 'External Sector - 3.4. Travel - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - monthly - debit
        # 3. 4. 1. Travel - business
        ('22743', 'External Sector - 3.4.1. Travel - business - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - business - monthly - net
        ('22744', 'External Sector - 3.4.1. Travel - business - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - business - monthly - credit
        ('22745', 'External Sector - 3.4.1. Travel - business - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - business - monthly - debit
        # 3. 4. 2. Travel - personal
        ('22746', 'External Sector - 3.4.2. Travel - personal - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - monthly - net
        ('22747', 'External Sector - 3.4.2. Travel - personal - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - monthly - credit
        ('22748', 'External Sector - 3.4.2. Travel - personal - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - monthly - debit
        # 3. 4. 2. 1. Health-related
        ('22749', 'External Sector - 3.4.2.1. Travel - personal - health-related - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - health-related - monthly - net
        ('22750', 'External Sector - 3.4.2.1. Travel - personal - health-related - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - health-related - monthly - credit
        ('22751', 'External Sector - 3.4.2.1. Travel - personal - health-related - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - health-related - monthly - debit
        # 3. 4. 2. 2. Education-related
        ('22752', 'External Sector - 3.4.2.2. Travel - personal - education-related - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - education-related - monthly - net
        ('22753', 'External Sector - 3.4.2.2. Travel - personal - education-related - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - education-related - monthly - credit
        ('22754', 'External Sector - 3.4.2.2. Travel - personal - education-related - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - education-related - monthly - debit
        # 3. 4. 2. 3. Tourism and others
        ('22755', 'External Sector - 3.4.2.3. Travel - personal - other, including tourism - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - other, including tourism - monthly - net
        ('22756', 'External Sector - 3.4.2.3. Travel - personal - other, including tourism - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - other, including tourism - monthly - credit
        ('22757', 'External Sector - 3.4.2.3. Travel - personal - other, including tourism - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - personal - other, including tourism - monthly - debit
        # 3. 4. 3. International cards
        ('22758', 'External Sector - 3.4.3. Travel - settled by international cards - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - settled by international cards - monthly - net
        ('22759', 'External Sector - 3.4.3. Travel - settled by international cards - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - settled by international cards - monthly - credit
        ('22760', 'External Sector - 3.4.3. Travel - settled by international cards - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Travel - settled by international cards - monthly - debit
        # 3. 5. Construction
        ('22761', 'External Sector - 3.5. Construction - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Construction - monthly - net
        ('22762', 'External Sector - 3.5. Construction - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Construction - monthly - credit
        ('22763', 'External Sector - 3.5. Construction - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Construction - monthly - debit
        # 3. 6. Insurance and pension
        ('22764', 'External Sector - 3.6. Insurance and pension services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Insurance and pension services - monthly - net
        ('22765', 'External Sector - 3.6. Insurance and pension services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Insurance and pension services - monthly - credit
        ('22766', 'External Sector - 3.6. Insurance and pension services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Insurance and pension services - monthly - debit
        # 3. 7. Financial services
        ('22767', 'External Sector - 3.7. Financial services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial services - monthly - net
        ('22768', 'External Sector - 3.7. Financial services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial services - monthly - credit
        ('22769', 'External Sector - 3.7. Financial services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial services - monthly - debit
        # 3. 7. 1. Explicitly charged
        ('22770', 'External Sector - 3.7.1. Financial services - explicitly charged and other financial services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial services - explicitly charged and other financial services - monthly - net
        ('22771', 'External Sector - 3.7.1. Financial services - explicitly charged and other financial services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial services - explicitly charged and other financial services - monthly - credit
        ('22772', 'External Sector - 3.7.1. Financial services - explicitly charged and other financial services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial services - explicitly charged and other financial services - monthly - debit
        # 3. 7. 2. Indirectly measured
        ('22773', 'External Sector - 3.7.2. Financial intermediation services indirectly measured - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial intermediation services indirectly measured - monthly - net
        ('22774', 'External Sector - 3.7.2. Financial intermediation services indirectly measured - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial intermediation services indirectly measured - monthly - credit
        ('22775', 'External Sector - 3.7.2. Financial intermediation services indirectly measured - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Financial intermediation services indirectly measured - monthly - debit
        # 3. 8. Intellectual property
        ('22776', 'External Sector - 3.8. Charges for the use of intellectual property n.i.e. - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Charges for the use of intellectual property n.i.e. - monthly - net
        ('22777', 'External Sector - 3.8. Charges for the use of intellectual property n.i.e. - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Charges for the use of intellectual property n.i.e. - monthly - credit
        ('22778', 'External Sector - 3.8. Charges for the use of intellectual property n.i.e. - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Charges for the use of intellectual property n.i.e. - monthly - debit
        # 3. 9. Telecom
        ('22779', 'External Sector - 3.9. Telecommunications, computer, and information services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Telecommunications, computer, and information services - monthly - net
        ('22780', 'External Sector - 3.9. Telecommunications, computer, and information services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Telecommunications, computer, and information services - monthly - credit
        ('22781', 'External Sector - 3.9. Telecommunications, computer, and information services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Telecommunications, computer, and information services - monthly - debit
        # 3. 10. Leasing
        ('22782', 'External Sector - 3.10. Operating leasing services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Operating leasing services - monthly - net
        ('22783', 'External Sector - 3.10. Operating leasing services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Operating leasing services - monthly - credit
        ('22784', 'External Sector - 3.10. Operating leasing services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Operating leasing services - monthly - debit
        # 3. 11. Architecture and engineering
        ('22785', 'External Sector - 3.11. Other business services, including architecture and engineering - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Other business services, including architecture and engineering - monthly - net
        ('22786', 'External Sector - 3.11. Other business services, including architecture and engineering - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Other business services, including architecture and engineering - monthly - credit
        ('22787', 'External Sector - 3.11. Other business services, including architecture and engineering - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Other business services, including architecture and engineering - monthly - debit
        # 3. 12. Cultural and recreational
        ('22788', 'External Sector - 3.12. Personal, cultural, and recreational services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Personal, cultural, and recreational services - monthly - net
        ('22789', 'External Sector - 3.12. Personal, cultural, and recreational services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Personal, cultural, and recreational services - monthly - credit
        ('22790', 'External Sector - 3.12. Personal, cultural, and recreational services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Personal, cultural, and recreational services - monthly - debit
        # 3. 12. 1. Audiovisual
        ('22791', 'External Sector - 3.12.1. Audiovisual services and related - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Audiovisual services and related - monthly - net
        ('22792', 'External Sector - 3.12.1. Audiovisual services and related - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Audiovisual services and related - monthly - credit
        ('22793', 'External Sector - 3.12.1. Audiovisual services and related - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Audiovisual services and related - monthly - debit
        # 3. 12. 2. Health and Education
        ('22794', 'External Sector - 3.12.2. Health, education and other cultural, personal and recreational services - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Health, education and other cultural, personal and recreational services - monthly - net
        ('22795', 'External Sector - 3.12.2. Health, education and other cultural, personal and recreational services - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - ... - credit
        ('22796', 'External Sector - 3.12.2. Health, education and other cultural, personal and recreational services - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - ... - debit
        # 3. 13. Government goods and services
        ('22797', 'External Sector - 3.13. Government goods and services n.i.e. - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Government goods and services n.i.e. - monthly - net
        ('22798', 'External Sector - 3.13. Government goods and services n.i.e. - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Government goods and services n.i.e. - monthly - credit
        ('22799', 'External Sector - 3.13. Government goods and services n.i.e. - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Government goods and services n.i.e. - monthly - debit

        # 4. Primary Income
        ('22800', 'External Sector - 4. Primary income - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Primary income - monthly - net
        ('22801', 'External Sector - 4. Primary income - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Primary income - monthly - credit
        ('22802', 'External Sector - 4. Primary income - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Primary income - monthly - debit
        # 4. 1. Compensation of employees
        ('22803', 'External Sector - 4.1. Compensation of employees - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Compensation of employees - monthly - net
        ('22804', 'External Sector - 4.1. Compensation of employees - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - ... - credit
        ('22805', 'External Sector - 4.1. Compensation of employees - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - ... - debit
        # 4. 2. Investment income
        ('22806', 'External Sector - 4.2. Investment income - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Investment income - monthly - net
        ('22807', 'External Sector - 4.2. Investment income - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - ... - credit
        ('22808', 'External Sector - 4.2. Investment income - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - ... - debit
        # 4. 2. 1. Direct investment
        ('22809', 'External Sector - 4.2.1. Direct investment income - monthly - net (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - Direct investment income - monthly - net
        ('22810', 'External Sector - 4.2.1. Direct investment income - monthly - credit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - ... - credit
        ('22811', 'External Sector - 4.2.1. Direct investment income - monthly - debit (BCB-DSTAT)', 'Monthly'),  # BCB-DSTAT - ... - debit
        # 4. 2. 1. 1. Dividends
        ('22812', 'External Sector - 4.2.1.1. Direct investment income - Dividends remitted - monthly - net (BCB-DSTAT)', 'Monthly'),  # ...
        ('22813', 'External Sector - 4.2.1.1. Direct investment income - Dividends remitted - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22814', 'External Sector - 4.2.1.1. Direct investment income - Dividends remitted - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 2. 1. 2. Reinvested
        ('22815', 'External Sector - 4.2.1.2. Direct investment income Reinvested earnings - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22816', 'External Sector - 4.2.1.2. Direct investment income Reinvested earnings - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22817', 'External Sector - 4.2.1.2. Direct investment income Reinvested earnings - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 2. 1. 3. Intercompany loans
        ('22818', 'External Sector - 4.2.1.3. Direct investment income Interest on intercompany loans - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22819', 'External Sector - 4.2.1.3. Direct investment income Interest on intercompany loans - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22820', 'External Sector - 4.2.1.3. Direct investment income Interest on intercompany loans - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 2. 2. Portfolio investment
        ('22821', 'External Sector - 4.2.2. Portfolio investment income - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22822', 'External Sector - 4.2.2. Portfolio investment income - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22823', 'External Sector - 4.2.2. Portfolio investment income - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 2. 2. 1. Dividends
        ('22824', 'External Sector - 4.2.2.1. Portfolio investment income - Dividends - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22825', 'External Sector - 4.2.2.1. Portfolio investment income - Dividends - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22826', 'External Sector - 4.2.2.1. Portfolio investment income - Dividends - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 2. 2. 2. Securities abroad
        ('22827', 'External Sector - 4.2.2.2. Portfolio investment income - Interest on securities issued abroad - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22828', 'External Sector - 4.2.2.2. Portfolio investment income - Interest on securities issued abroad - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22829', 'External Sector - 4.2.2.2. Portfolio investment income - Interest on securities issued abroad - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 2. 2. 3. Securities in Brazil
        ('22830', 'External Sector - 4.2.2.3. Portfolio investment income - Interest on securities issued in Brazil - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 2. 2. 4. Other investment income
        ('22831', 'External Sector - 4.2.2.4. Other investment income - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22832', 'External Sector - 4.2.2.4. Other investment income - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22833', 'External Sector - 4.2.2.4. Other investment income - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 3. Reserve assets
        ('22834', 'External Sector - 4.3. Reserve assets - monthly - credit (BCB-DSTAT)', 'Monthly'),
        # 4. 4. Other primary income
        ('22835', 'External Sector - 4.4. Other primary income - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22836', 'External Sector - 4.4. Other primary income - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22837', 'External Sector - 4.4. Other primary income - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 5. Secondary income
        ('22838', 'External Sector - 4.5. Secondary income - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22839', 'External Sector - 4.5. Secondary income - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22840', 'External Sector - 4.5. Secondary income - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 5. 1. General government
        ('22841', 'External Sector - 4.5.1. Secondary income - General government - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22842', 'External Sector - 4.5.1. Secondary income - General government - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22843', 'External Sector - 4.5.1. Secondary income - General government - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 5. 2. Corporations & households
        ('22844', 'External Sector - 4.5.2. Secondary income - Financial corporations, nonfinancial corporations, households, and NPISHs - monthly - net (BCB-DSTAT)', 'Monthly'),
        # 4. 5. 3. Personal transfers
        ('22845', 'External Sector - 4.5.3. Secondary income - Personal transfers - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22846', 'External Sector - 4.5.3. Secondary income - Personal transfers - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22847', 'External Sector - 4.5.3. Secondary income - Personal transfers - monthly - debit (BCB-DSTAT)', 'Monthly'),
        # 4. 5. 4. Others
        ('22848', 'External Sector - 4.5.4. Secondary income - Other current transfers - monthly - net (BCB-DSTAT)', 'Monthly'),
        ('22849', 'External Sector - 4.5.4. Secondary income - Other current transfers - monthly - credit (BCB-DSTAT)', 'Monthly'),
        ('22850', 'External Sector - 4.5.4. Secondary income - Other current transfers - monthly - debit (BCB-DSTAT)', 'Monthly'),

        ],}


@dataclass(frozen=True)
class IndicatorsConfig:
    """
    """

    # 
    endpoint: Mapping[str, str] = field(default_factory=lambda:ENDPOINT)
    source: Mapping[str, List[Tuple[str, str, str]]] = field(default_factory=lambda: SOURCE)



def load_indicators_config() -> IndicatorsConfig:
    """Factory function to load repository configuration.

    Returns:
        RepositoryConfig: Initialized with default batch size and
        persistence threshold.
    """
    # Construct and return repository configuration with defaults
    return IndicatorsConfig(
        endpoint=ENDPOINT,
        source=SOURCE,
    )
