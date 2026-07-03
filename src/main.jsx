import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import IngredientSearchApp from './IngredientSearchApp.jsx'
import Onboarding from './Onboarding.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <IngredientSearchApp />
    <Onboarding />
  </React.StrictMode>,
)
