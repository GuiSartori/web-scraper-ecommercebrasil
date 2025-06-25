# Importe as bibliotecas necessárias
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
import time
import os
from datetime import datetime

# Importa exceções
from selenium.common.exceptions import *

# IMPORTAÇÃO ADICIONAL PARA SALVAR EM EXCEL
import pandas as pd

def main():
    dados_noticias = []
    output_dir = os.path.join('src', 'news')
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_name = f'noticias_ecommercebrasil_{timestamp}.xlsx'
    file_path = os.path.join(output_dir, file_name)

    os.makedirs(output_dir, exist_ok=True)
    
    chromedriver_path = r"src\utils\chromedriver.exe"
    service = ChromeService(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service)

    try:
        driver.get("https://www.ecommercebrasil.com.br/marketplace/mais-recentes")
        driver.maximize_window()
        
        wait = WebDriverWait(driver, 20)
        cookit_btn_xpath = '//*[@id="hs-eu-confirmation-button"]'
        cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, cookit_btn_xpath)))
        cookie_button.click()

        wait.until(EC.presence_of_element_located((By.XPATH, "//h4[@class='content-body-title']/a")))
        links_noticias = driver.find_elements(By.XPATH, "//h4[@class='content-body-title']/a")
        urls = [link.get_attribute('href') for link in links_noticias]

        print(f"Encontrados {len(urls)} links de notícias. Iniciando extração...")
        print("-" * 30)

        for i, url in enumerate(urls, 1):
            try:
                driver.switch_to.new_window('tab')
                driver.get(url)

                # --- MODIFICAÇÃO PRINCIPAL AQUI ---

                # 1. Seletor agora busca TODOS os parágrafos <p> DENTRO do article-content
                seletor_paragrafos = (By.XPATH, '//*[@class="article-content"]//p')
                
                # 2. Espera até que o PRIMEIRO parágrafo esteja presente na página
                wait.until(EC.presence_of_element_located(seletor_paragrafos))

                # Extrai os dados do cabeçalho da matéria
                titulo = driver.find_element(By.XPATH, "//h1[@class='article-title']").text
                print(f'Título capturado: {titulo}')

                data_suja = driver.find_element(By.XPATH, "//header[@class='article-header']//time").text
                print('data captada com sucesso')
                
                data_limpa = data_suja.strip().replace("Em ", "")
                print('data limpa captada com sucesso')

                # 3. Coleta o texto de CADA parágrafo individualmente
                elementos_paragrafo = driver.find_elements(*seletor_paragrafos)

                print('Texto de cada parágrafo coletado com sucesso')
                
                # 4. Cria uma lista com o texto de cada parágrafo (e ignora parágrafos vazios)
                lista_de_textos = [p.text for p in elementos_paragrafo if p.text and p.text.strip()]
                
                # 5. Junta todos os textos em uma única variável, separados por quebras de linha
                texto_completo = "\n\n".join(lista_de_textos)

                # Se, por algum motivo, texto_completo estiver vazio, loga um aviso
                if not texto_completo:
                    print(f"AVISO: Nenhum texto de parágrafo encontrado para: {titulo}")

                dados_noticias.append({
                    'Título': titulo,
                    'Data': data_limpa,
                    'Link': url,
                    'Texto': texto_completo
                })
                print(f"OK ({i}/{len(urls)}): {titulo}")

            except Exception as e:
                # Se ocorrer um erro (ex: Timeout), o print mostrará qual foi
                print(f"ERRO ao processar o link {url}: {e.__class__.__name__}")
            
            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)

        print("-" * 30)
        print('Extração de dados finalizada.')

    except Exception as e:
        print(f"Ocorreu um erro geral durante a extração: {e.__class__.__name__} - {e}")
    
    finally:
        print("Fechando o navegador.")
        driver.quit()

    if not dados_noticias:
        print("Nenhum dado foi coletado. A planilha não será gerada.")
    else:
        try:
            print(f"Salvando {len(dados_noticias)} notícias na planilha...")
            df = pd.DataFrame(dados_noticias)
            df.to_excel(file_path, index=False, engine='openpyxl')
            print(f"Planilha salva com sucesso em: {file_path}")
        except Exception as e:
            print(f"Ocorreu um erro ao salvar a planilha: {e.__class__.__name__} - {e}")

if __name__ == "__main__":
    main()
