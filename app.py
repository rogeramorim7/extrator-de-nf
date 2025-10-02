import streamlit as st # type: ignore
import pandas as pd # type: ignore
import io
import tempfile
import warnings

# Checagem de dependências
try:
    import camelot # type: ignore
    CAMELot_AVAILABLE = True
    CAMELot_VERSION = camelot.__version__
except ImportError:
    CAMELot_AVAILABLE = False

try:
    import fitz  # type: ignore # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract # type: ignore
    from PIL import Image # type: ignore
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import xlsxwriter # type: ignore
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# Sidebar: status das dependências
st.sidebar.header("Verificação de Dependências")
st.sidebar.success(f"Camelot v{CAMELot_VERSION}" if CAMELot_AVAILABLE else "Camelot não instalado (pip install camelot-py[cv])")
st.sidebar.success("PyMuPDF disponível" if PYMUPDF_AVAILABLE else "PyMuPDF não instalado (pip install PyMuPDF)")
st.sidebar.success("pytesseract disponível" if TESSERACT_AVAILABLE else "pytesseract/Pillow não instalados (pip install pytesseract Pillow)")
st.sidebar.success("XlsxWriter disponível" if XLSX_AVAILABLE else "XlsxWriter não instalado (pip install XlsxWriter)")

st.title("Extrator de Itens de NF-e (PDF)")

# Ajuste do executável do Tesseract (Windows)
if TESSERACT_AVAILABLE:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Funções de extração ---

def extrair_pdf_camelot(pdf_path):
    """Extrai tabelas do PDF usando Camelot"""
    try:
        tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
        if tables.n == 0:
            tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")

        if tables.n == 0:
            return pd.DataFrame({"Erro": ["Nenhuma tabela encontrada pelo Camelot"]})

        # Mantém apenas tabelas que parecem ser de produtos (com várias colunas)
        dfs = [t.df for t in tables if t.df.shape[1] >= 5]
        if not dfs:
            return pd.DataFrame({"Erro": ["Nenhuma tabela de produtos encontrada"]})

        df = pd.concat(dfs, ignore_index=True)
        df.columns = df.iloc[0]  # primeira linha como cabeçalho
        df = df.drop(0).reset_index(drop=True)
        return df

    except Exception as e:
        return pd.DataFrame({"Erro": [f"Camelot falhou: {e}"]})


def extrair_por_ocr(pdf_path):
    """Fallback: usa OCR caso Camelot não funcione"""
    if not (PYMUPDF_AVAILABLE and TESSERACT_AVAILABLE):
        return pd.DataFrame({"Erro": ["OCR indisponível (instale PyMuPDF e pytesseract)"]})
    doc = fitz.open(pdf_path)
    texto = ""
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        texto += pytesseract.image_to_string(img, lang="por")
    return pd.DataFrame({"Texto Extraído (OCR)": [texto]})


import tabula # type: ignore

import tabula # type: ignore

def extrair_itens(pdf_path):
    try:
        # Extrai todas as tabelas do PDF
        tables = tabula.read_pdf(
            pdf_path,
            pages="all",
            multiple_tables=True,
            lattice=True,
            encoding="latin-1"  # força Latin-1
        )

        if not tables:
            tables = tabula.read_pdf(
                pdf_path,
                pages="all",
                multiple_tables=True,
                stream=True,
                encoding="latin-1"
            )

        if not tables:
            return pd.DataFrame({"Erro": ["Nenhuma tabela encontrada no PDF"]})

        # Filtra só tabelas de produtos (com várias colunas)
        dfs = [t for t in tables if t.shape[1] >= 5]
        if not dfs:
            return pd.DataFrame({"Erro": ["Nenhuma tabela de produtos encontrada"]})

        df = pd.concat(dfs, ignore_index=True)

        # Normaliza colunas e remove sujeira
        df = df.dropna(how="all", axis=1)  # remove colunas totalmente vazias
        df = df.dropna(how="all", axis=0)  # remove linhas totalmente vazias
        df = df.applymap(lambda x: str(x).encode("latin-1", "ignore").decode("latin-1") if isinstance(x, str) else x)
        df = df.reset_index(drop=True)

        return df

    except Exception as e:
        return pd.DataFrame({"Erro": [f"Falha no Tabula: {e}"]})
    

def exibir_resultado(df):
    st.subheader("Itens Extraídos")
    df_display = df.fillna("").astype(str)
    df_display.columns = [str(c) for c in df_display.columns]
    st.dataframe(df_display)

    if "Erro" in df.columns:
        st.error(df.loc[0, "Erro"])
    elif XLSX_AVAILABLE:
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Itens")
        towrite.seek(0)
        st.download_button(
            label="Exportar para Excel",
            data=towrite.getvalue(),
            file_name="itens_nf.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Para exportar, instale XlsxWriter")


# Upload de PDF
st.sidebar.header("Upload de NF-e (PDF)")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo PDF", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp.flush()
        df_itens = extrair_itens(tmp.name)
    exibir_resultado(df_itens)
