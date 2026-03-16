# CEDEAR Dashboard 📊

Dashboard web para monitorear acciones que cotizan en NYSE/NASDAQ y tienen **CEDEAR en BYMA**.  
Los datos se actualizan automáticamente cada día hábil usando **Yahoo Finance** vía **GitHub Actions**.

## 🚀 Cómo publicarlo en 5 minutos

### 1. Crear el repositorio en GitHub
1. Creá un repositorio nuevo en GitHub (puede ser público o privado)
2. Subí todos los archivos de este proyecto

```bash
git init
git add .
git commit -m "Initial commit: CEDEAR Dashboard"
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

### 2. Activar GitHub Pages
1. En tu repositorio: **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / `/(root)`
4. Guardá → en unos minutos vas a tener la URL `https://TU_USUARIO.github.io/TU_REPO`

### 3. Dar permisos a GitHub Actions
1. **Settings → Actions → General**
2. En "Workflow permissions" seleccioná **Read and write permissions**
3. Guardá

### 4. Correr el workflow por primera vez (para tener datos)
1. Ir a **Actions → "Actualizar datos de mercado"**
2. Click en **Run workflow** → **Run workflow**
3. Esperá ~2 minutos a que termine
4. Recargá el dashboard → ¡ya tiene datos reales!

---

## ⏰ Actualización automática

El workflow corre **de lunes a viernes a las 22:00 UTC** (19:00 hora de Buenos Aires),  
que es después del cierre del mercado NYSE (16:00 ET = 21:00 UTC).

Para cambiar el horario, editá el `cron` en `.github/workflows/update_data.yml`:

```yaml
- cron: "0 22 * * 1-5"   # UTC — ajustá según tu zona
```

---

## 🧩 Estructura del proyecto

```
cedear-dashboard/
├── index.html                        # Dashboard (GitHub Pages lo sirve)
├── data/
│   └── market_data.json              # Generado por el script (no editar)
├── scripts/
│   └── fetch_data.py                 # Descarga datos de Yahoo Finance
└── .github/
    └── workflows/
        └── update_data.yml           # GitHub Action (cron diario)
```

---

## 📈 Acciones incluidas (~50 CEDEARs)

| Sector | Tickers |
|--------|---------|
| Tecnología | AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, NFLX, ORCL, CRM, INTC, AMD, QCOM, ADBE, PYPL, UBER, SPOT, SHOP |
| Finanzas | JPM, GS, BAC, C, WFC, MS, BLK, AXP, V, MA |
| Energía | XOM, CVX, COP, SLB, BP |
| Consumo | WMT, KO, PG, MCD, NKE, SBUX, DIS, AMGN |
| Salud | JNJ, PFE, MRK, ABBV, UNH, LLY |
| Industrial | CAT, BA, GE, MMM, HON |

Para agregar o quitar tickers, editá el diccionario `CEDEARS` en `scripts/fetch_data.py`.

---

## 📊 Indicadores incluidos

- **Precio USD** (cierre del día) + variación porcentual
- **Precio ARS referencial** (TC implícito CEDEAR)
- **RSI (14)** con señal sobrecompra/sobreventa
- **MACD (12/26/9)** línea, señal e histograma
- **Medias móviles** SMA 20, 50, 200
- **Gráfico histórico** últimos 90 días
- **Máx./Mín. 52 semanas**, volumen, cierre anterior

---

## ⚠️ Notas importantes

- Los **precios ARS** son referenciales basados en un TC implícito fijo (`TC_REF` en `index.html`).
  Para tener el TC real podés integrar la API de [dolarapi.com](https://dolarapi.com) o similar.
- Yahoo Finance puede tener demoras de 15-20 minutos en datos intradía; este dashboard usa **datos de cierre**.
- El uso de `yfinance` está sujeto a los términos de servicio de Yahoo Finance.

---

## 🔧 Desarrollo local

Para probar localmente, necesitás un servidor HTTP (no funciona con `file://` por restricciones CORS):

```bash
# Python
python -m http.server 8000
# o Node.js
npx serve .
```

Para regenerar los datos localmente:
```bash
pip install yfinance pandas
python scripts/fetch_data.py
```
