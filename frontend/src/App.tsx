import { useState } from 'react'
import Dashboard from './components/Dashboard'
import TypedStrategyDashboard from './components/TypedStrategyDashboard'
import './App.css'

function App() {
  const [useTypedDashboard, setUseTypedDashboard] = useState(false)

  return (
    <div className="App">
      {/* Dashboard Toggle */}
      <div className="fixed top-4 right-4 z-50">
        <div className="bg-white shadow-lg rounded-lg p-3 border">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-700">Dashboard:</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={useTypedDashboard}
                onChange={(e) => setUseTypedDashboard(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
            <span className="text-sm text-gray-600">
              {useTypedDashboard ? 'SQLModel v2' : 'Legacy v1'}
            </span>
          </div>
        </div>
      </div>

      {/* Render appropriate dashboard */}
      {useTypedDashboard ? <TypedStrategyDashboard /> : <Dashboard />}
    </div>
  )
}

export default App
