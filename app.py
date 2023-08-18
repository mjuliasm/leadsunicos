import streamlit as st
import requests
import pandas as pd
from dateutil.parser import parse
import altair as alt

# Função para obter os registros usando apenas o token_exact
def get_records(token, start_date=None, end_date=None, skip=0):
    base_url = "https://api.exactspotter.com/v3/callsHistory"
    headers = {
        'Content-Type': 'application/json',
        'token_exact': token
    }
    page_size = 100
    all_records = []

    while True:
        params = {
            '$top': page_size,
            '$skip': skip
        }

        if start_date:
            params['startDate'] = start_date.strftime('%Y-%m-%dT%H:%M:%S')
        if end_date:
            params['endDate'] = end_date.strftime('%Y-%m-%dT%H:%M:%S')

        try:
            response = requests.get(base_url, headers=headers, params=params)
            data = response.json()

            if data is not None and data.get('value'):
                all_records.extend(data['value'])
                skip += page_size
            else:
                # Não há mais registros ou 'data' é None, sair do loop
                break
        except Exception as e:
            print(f"Erro ao recuperar registros: {e}")
            break

    return all_records

def main():
    st.title("Leads Únicos por Dia e Usuário")
    
    # Solicitar token_exact e filtros de data na barra lateral
    token_exact = st.sidebar.text_input("Insira o token_exact:", type="password")
    selected_start_date = st.sidebar.date_input("Selecione a data de início")
    selected_end_date = st.sidebar.date_input("Selecione a data de fim")

    # Verificar se o token_exact é válido e se o botão "Calcular" foi pressionado
    if st.sidebar.button("Faça a mágica acontecer") and token_exact:
        if selected_start_date > selected_end_date:
            st.sidebar.error("A data de início não pode ser maior que a data de fim.")
            return

        try:
            records = get_records(
                token=token_exact,
                start_date=selected_start_date,
                end_date=selected_end_date
            )
            df = pd.DataFrame(records)
            df = df[['leadId', 'startDate', 'userName', 'manualSet']]
            
            # Fazer o parsing correto da coluna startDate
            df['startDate'] = df['startDate'].apply(parse)
            df['Data'] = df['startDate'].dt.date  # Manter o formato original
            
            # Filtrar por data selecionada
            df = df[(df['Data'] >= selected_start_date) & (df['Data'] <= selected_end_date)]
            
            # Contar os leadId únicos por dia e userName
            agrupado = df.groupby(['Data', 'userName'])['leadId'].nunique().reset_index()
            agrupado.rename(columns={'leadId': 'Quantidade', 'userName': 'Usuário'}, inplace=True)
            
            # Gráfico de linhas usando Altair
            chart = alt.Chart(agrupado).mark_line().encode(
                x=alt.X('Data:O', title='Data'),
                y=alt.Y('Quantidade:Q', title='Quantidade'),
                color='Usuário:N'
            ).properties(
                width=800,
                height=400
            ).configure_axis(
                labelFontSize=12,
                titleFontSize=14,
                labelAngle=-45
            )
            
            st.write("Evolução dos Leads Únicos por Dia e Usuário:")
            st.altair_chart(chart)
            
            # Tabela com os dados dos Leads Únicos por Dia e Usuário
            st.write("Dados dos Leads Únicos por Dia e Usuário:")
            st.table(agrupado.pivot(index='Usuário', columns='Data', values='Quantidade').fillna(0))

        except Exception as e:
            st.error(f"Erro ao recuperar registros: {e}")
    elif token_exact:
        st.sidebar.warning("Clique no botão 'Faça a mágica acontecer' para visualizar os resultados.")
    else:
        st.sidebar.warning("Insira um token_exact válido para acessar os dados.")

if __name__ == "__main__":
    main()
