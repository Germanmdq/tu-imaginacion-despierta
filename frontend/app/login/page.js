"use client";

import { createClient } from '@/utils/supabase/client'
import { useState } from 'react'

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const supabase = createClient()

  const handleLogin = async (provider) => {
    if (provider === 'apple') {
      alert("No disponible por el momento, ingresa con tu cuenta de Google o mail personal.");
      return;
    }

    setIsLoading(true)
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    
    if (error) {
      console.error('Error logging in:', error.message)
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f3f4f6] flex items-center justify-center p-4">
      <div className="bg-white max-w-md w-full p-8 rounded-[2.5rem] shadow-xl border border-gray-200">
        
        <div className="flex flex-col items-center mb-10">
          <LogoTID className="h-16 text-gray-900 mb-6" />
          <p className="text-gray-500 text-center text-sm font-medium">Tu biblioteca metafísica y asistente personal.</p>
        </div>

        <div className="space-y-4">
          <button 
            onClick={() => handleLogin('google')}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-200 text-gray-800 py-4 px-6 rounded-2xl hover:bg-gray-50 transition-colors font-bold disabled:opacity-50"
          >
            <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" className="w-6 h-6" />
            Continuar con Google
          </button>
          
          <button 
            onClick={() => handleLogin('apple')}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-black text-white py-4 px-6 rounded-2xl hover:bg-gray-900 transition-colors font-bold disabled:opacity-50"
          >
            <svg viewBox="0 0 384 512" className="w-5 h-5 fill-current" xmlns="http://www.w3.org/2000/svg">
              <path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.1-44.6-35.9-2.8-74.3 22.7-93.1 22.7-18.9 0-46.2-21-76-21-44.2 0-85.9 25.7-109.3 66.8-47 82.2-12 216 33.7 282.8 22.2 32.5 48.3 69 82.3 67.8 32-.9 45-19.8 84-19.8 38.8 0 50.8 19.8 84.4 19.3 34.6-.5 57.3-33.6 79-66.2 26-38.3 36.8-75.3 37.4-77.2-1-1.3-68.2-26.3-68.3-105.8zm-119.3-195c21.2-25.5 35.6-60.8 31.7-96-30.8 1.2-68.4 20.6-90 46-19.2 22.3-35.7 58.7-30.9 93 33.5 2.6 67.9-17.5 89.2-43z"/>
            </svg>
            Continuar con Apple
          </button>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          Al iniciar sesión, aceptas nuestros Términos de Servicio y Política de Privacidad.
        </div>
      </div>
    </div>
  )
}

const LogoTID = ({ className }) => (
  <svg viewBox="0 0 145 50" className={className} fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="145" height="12" />
    <rect x="20" y="12" width="12" height="38" />
    <rect x="65" y="12" width="12" height="38" />
    <path d="M 95 12 V 50 H 110 A 19 19 0 0 0 110 12 Z M 107 24 H 110 A 7 7 0 0 1 110 38 H 107 Z" fillRule="evenodd" />
  </svg>
);
