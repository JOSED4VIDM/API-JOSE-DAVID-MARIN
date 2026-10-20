import { useCallback, useEffect, useState } from 'react'
import './App.css'

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim()
const API_URL = configuredApiUrl
  ? configuredApiUrl.startsWith('http')
    ? configuredApiUrl.replace(/\/+$/, '')
    : `https://${configuredApiUrl.replace(/\/+$/, '')}`
  : 'http://127.0.0.1:8000'

async function readResponse(response) {
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = Array.isArray(body?.detail)
      ? body.detail.map((error) => error.msg).join(', ')
      : body?.detail
    throw new Error(detail || `Error HTTP ${response.status}`)
  }
  return body
}

function App() {
  const [aprendices, setAprendices] = useState([])
  const [estadoApi, setEstadoApi] = useState('comprobando')
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')
  const [consultaId, setConsultaId] = useState('')
  const [aprendizConsultado, setAprendizConsultado] = useState(null)

  const cargarAprendices = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/aprendices`)
      const data = await readResponse(response)
      setAprendices(data)
      setEstadoApi('conectada')
    } catch (err) {
      setEstadoApi('desconectada')
      setError(
        err instanceof TypeError
          ? 'No se pudo conectar. Confirma que FastAPI esté iniciado en http://127.0.0.1:8000.'
          : err.message,
      )
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    let activo = true
    fetch(`${API_URL}/api/aprendices`)
      .then(readResponse)
      .then((data) => {
        if (!activo) return
        setAprendices(data)
        setEstadoApi('conectada')
      })
      .catch((err) => {
        if (!activo) return
        setEstadoApi('desconectada')
        setError(
          err instanceof TypeError
            ? 'No se pudo conectar. Confirma que FastAPI esté iniciado en http://127.0.0.1:8000.'
            : err.message,
        )
      })
      .finally(() => {
        if (activo) setCargando(false)
      })
    return () => {
      activo = false
    }
  }, [])

  function actualizarLista() {
    setCargando(true)
    setError('')
    void cargarAprendices()
  }

  async function registrarAprendiz(event) {
    event.preventDefault()
    setGuardando(true)
    setMensaje('')
    setError('')
    const form = event.currentTarget
    const datos = Object.fromEntries(new FormData(form))

    try {
      const response = await fetch(`${API_URL}/api/aprendices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos),
      })
      await readResponse(response)
      form.reset()
      setMensaje('Aprendiz registrado correctamente.')
      setCargando(true)
      setError('')
      await cargarAprendices()
    } catch (err) {
      setError(err.message)
    } finally {
      setGuardando(false)
    }
  }

  async function consultarAprendiz(event) {
    event.preventDefault()
    setError('')
    setMensaje('')
    setAprendizConsultado(null)
    try {
      const response = await fetch(
        `${API_URL}/api/aprendices/${encodeURIComponent(consultaId)}`,
      )
      setAprendizConsultado(await readResponse(response))
    } catch (err) {
      setError(err instanceof TypeError ? 'No se pudo conectar con la API.' : err.message)
    }
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Aprende, inicio">
          <span className="brand-mark">A</span>
          <span>Aprende<span className="brand-light"> / API</span></span>
        </a>
        <div className="topbar-actions">
          <span className={`api-status ${estadoApi}`}>
            <span className="status-dot" />
            API {estadoApi === 'conectada' ? 'conectada' : estadoApi === 'desconectada' ? 'sin conexión' : 'conectando'}
          </span>
          <a className="docs-link" href={`${API_URL}/docs`} target="_blank" rel="noreferrer">
            Documentación <span aria-hidden="true">↗</span>
          </a>
        </div>
      </header>

      <section className="intro">
        <div className="eyebrow"><span /> PANEL DE ADMINISTRACIÓN</div>
        <h1>Gestión de <span>aprendices.</span></h1>
        <p>Registra y consulta aprendices conectados directamente con tu API.</p>
      </section>

      <section className="dashboard" aria-label="Administración de aprendices">
        <div className="panel form-panel">
          <div className="panel-heading">
            <div>
              <span className="section-number">01 / REGISTRO</span>
              <h2>Nuevo aprendiz</h2>
            </div>
            <span className="heading-icon" aria-hidden="true">＋</span>
          </div>
          <form onSubmit={registrarAprendiz} className="learner-form">
            <label>
              Nombre completo
              <input name="nombre" type="text" placeholder="Ej. Ana Pérez" maxLength="100" required />
            </label>
            <label>
              Correo electrónico
              <input name="correo" type="email" placeholder="ana@correo.com" required />
            </label>
            <label>
              Programa de formación
              <input name="programa" type="text" placeholder="Ej. Desarrollo de software" maxLength="120" required />
            </label>
            <button className="primary-button" type="submit" disabled={guardando || estadoApi !== 'conectada'}>
              {guardando ? 'Guardando…' : 'Registrar aprendiz'} <span aria-hidden="true">→</span>
            </button>
          </form>
        </div>

        <div className="panel lookup-panel">
          <div className="panel-heading">
            <div>
              <span className="section-number">02 / BÚSQUEDA</span>
              <h2>Consulta por ID</h2>
            </div>
            <span className="heading-icon search-icon" aria-hidden="true">⌕</span>
          </div>
          <form className="lookup-form" onSubmit={consultarAprendiz}>
            <label htmlFor="learner-id">Encuentra un registro específico</label>
            <div className="lookup-control">
              <input
                id="learner-id"
                type="number"
                min="1"
                placeholder="Escribe el ID"
                value={consultaId}
                onChange={(event) => setConsultaId(event.target.value)}
                required
              />
              <button type="submit" disabled={estadoApi !== 'conectada'} aria-label="Buscar aprendiz">→</button>
            </div>
          </form>
          {aprendizConsultado && (
            <div className="lookup-result">
              <span className="result-id">#{aprendizConsultado.id}</span>
              <div><strong>{aprendizConsultado.nombre}</strong><span>{aprendizConsultado.correo}</span></div>
              <span className="result-program">{aprendizConsultado.programa}</span>
            </div>
          )}
          {!aprendizConsultado && (
            <p className="lookup-hint">Ingresa el ID para ver los datos de un aprendiz.</p>
          )}
        </div>
      </section>

      {error && (
        <div className="alert error-alert" role="alert">
          <span aria-hidden="true">!</span><p>{error}</p>
          {estadoApi === 'desconectada' && (
            <a href={`${API_URL}/docs`} target="_blank" rel="noreferrer">Ver API</a>
          )}
        </div>
      )}
      {mensaje && <div className="alert success-alert" role="status">✓ {mensaje}</div>}

      <section className="panel table-panel">
        <div className="table-heading">
          <div>
            <span className="section-number">DIRECTORIO</span>
            <h2>Aprendices registrados <span className="count-badge">{aprendices.length}</span></h2>
          </div>
          <button className="refresh-button" type="button" onClick={actualizarLista} disabled={cargando}>
            <span aria-hidden="true" className={cargando ? 'spin' : ''}>↻</span>
            {cargando ? 'Actualizando' : 'Actualizar'}
          </button>
        </div>

        <div className="table-scroll">
          <table>
            <thead>
              <tr><th>ID</th><th>Aprendiz</th><th>Correo electrónico</th><th>Programa</th></tr>
            </thead>
            <tbody>
              {aprendices.map((aprendiz) => (
                <tr key={aprendiz.id}>
                  <td data-label="ID"><span className="id-cell">#{aprendiz.id}</span></td>
                  <td data-label="Aprendiz"><strong className="name-cell">{aprendiz.nombre}</strong></td>
                  <td data-label="Correo electrónico">{aprendiz.correo}</td>
                  <td data-label="Programa"><span className="program-tag">{aprendiz.programa}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!cargando && aprendices.length === 0 && !error && (
            <div className="empty-state">
              <span aria-hidden="true">◌</span>
              <strong>Aún no hay aprendices</strong>
              <p>Cuando registres uno, aparecerá aquí.</p>
            </div>
          )}
          {cargando && <div className="loading-state">Cargando aprendices…</div>}
        </div>
        <footer className="table-footer">
          <span>Fuente: MongoDB Atlas</span>
          <a href={`${API_URL}/api/aprendices`} target="_blank" rel="noreferrer">Ver respuesta JSON ↗</a>
        </footer>
      </section>

      <footer className="page-footer">APRENDE <span>•</span> MONGODB ATLAS + FASTAPI</footer>
    </main>
  )
}

export default App
