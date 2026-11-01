# Sistem de Asistare a Deciziilor (SAD) - Analiza Riscului de Credit

Acest proiect este o aplicație de Business Intelligence și analiză a datelor dezvoltată în **Python** folosind **Streamlit** și **Plotly**, având ca scop asistarea deciziilor de acordare a creditelor pentru persoane fizice (Tema XX).

---

## 📁 Structura Proiectului

```text
Proiect_SAD_Credite/
├── .venv/                              # Mediul virtual Python (generat local)
├── data/
│   └── credit_risk_dataset_final_proiect.csv  # Setul de date
├── module/
│   ├── __init__.py                     # Fișier de inițializare pachet
│   ├── data_loader.py                  # Modul centralizat pentru citirea optimizată a datelor
│   ├── cerinta_1_pondere.py            # Modulul pentru ponderea tipurilor de credit
│   └── cerinta_4_dobanzi.py            # Modulul pentru analiza dobânzilor și a cererii
├── main.py                             # Punctul de intrare (Interfața Streamlit și Meniul principal)
└── README.md                           # Documentația proiectului
```

---

## ⚙️ Pași de instalare și configurare (Setup)

Asigură-te că ai instalat **Python** (versiunea 3.9 sau mai nouă) pe calculatorul tău.

### 1. Clonarea sau descărcarea proiectului

Deschide un terminal (Command Prompt, PowerShell sau terminalul din VS Code) în folderul principal al proiectului si cloneaza proiectul.

### 2. Crearea mediului virtual (.venv)

Rulează următoarea comandă în terminal pentru a crea un mediu virtual izolat:

- **Windows:**

```bash
python -m venv .venv
```

- **macOS / Linux:**

```bash
python3 -m venv .venv
```

### 3. Activarea mediului virtual

Înainte de a instala pachetele, activează mediul virtual:

- **Windows (Command Prompt):**

```cmd
.venv\Scripts\activate.bat
```

- **Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

- **macOS / Linux:**

```bash
source .venv/bin/activate
```

_(Vei observa prefixul `(.venv)` la începutul liniei în terminal, ceea ce indică faptul că mediul este activ)._

### 4. Instalarea dependențelor

Cu mediul virtual activat, instalează bibliotecile necesare (`streamlit`, `pandas`, `plotly`):

```bash
pip install -r requirements.txt
```

---

## 🚀 Rularea Aplicației

Pentru a porni serverul local Streamlit și a vizualiza interfața web, rulează:

```bash
streamlit run main.py
```

Comanda va deschide automat browserul tău, unde vei putea naviga prin meniurile laterale, explora grid-ul interactiv de date, aplica filtre și vizualiza graficele dinamice.
