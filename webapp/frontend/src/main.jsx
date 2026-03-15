// main.jsx
//
// Application entry point.
// Mounts the root React component into the #root div defined in index.html.
// React.StrictMode is enabled to surface potential issues during development
// (e.g. double-invoked effects, deprecated API usage); no effect in production.

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
