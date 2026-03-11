import { useState } from 'react'
import reactLogo from './assets/react.svg'
import appLogo from '/favicon.svg'
import PWABadge from './PWABadge.jsx'
import './App.css'
import Chat from './components/Chat.jsx'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <Chat />
    </div>
  )
}

export default App
