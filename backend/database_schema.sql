-- Script de inicialización para Supabase (PostgreSQL)
-- Copiar y pegar este código en el SQL Editor de tu proyecto en Supabase.

-- 1. Crear tabla de Usuarios (perfiles extendidos)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    nombre TEXT,
    is_premium BOOLEAN DEFAULT FALSE,
    preguntas_restantes INTEGER DEFAULT 3,
    telegram_id TEXT UNIQUE,
    whatsapp_id TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- 2. Crear tabla de Biblioteca (Textos de Neville)
CREATE TABLE IF NOT EXISTS public.library (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    titulo TEXT NOT NULL,
    autor TEXT NOT NULL,
    anio TEXT,
    texto_completo TEXT,
    etiquetas JSONB, -- Array de etiquetas guardado en formato JSON
    frases_destacadas JSONB, -- Array de frases destacadas
    explicaciones_metafisicas JSONB, -- Array de explicaciones
    testimonios JSONB, -- Array de objetos testimonio
    preguntas_verdadero_falso JSONB, -- Array de objetos para el quiz
    audio_url TEXT, -- Link al archivo MP3 (se subirá a Supabase Storage luego)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- 3. Crear tabla de Historial de Chat
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    origen TEXT DEFAULT 'web' CHECK (origen IN ('web', 'telegram', 'whatsapp')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- 4. Crear tabla de Favoritos
CREATE TABLE IF NOT EXISTS public.favorites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    library_id UUID REFERENCES public.library(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(user_id, library_id)
);

-- 5. Activar Row Level Security (Seguridad de base de datos)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.library ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;

-- 6. Políticas de Seguridad (Policies)
-- Todos pueden ver la biblioteca (catálogo público)
CREATE POLICY "Public Library Access" ON public.library FOR SELECT USING (true);

-- Los usuarios solo pueden ver y editar su propio perfil
CREATE POLICY "Users can view own profile" ON public.users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.users FOR UPDATE USING (auth.uid() = id);

-- Los usuarios solo pueden ver su propio historial de chat
CREATE POLICY "Users can view own chat history" ON public.chat_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own chat history" ON public.chat_history FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Los usuarios solo pueden ver y modificar sus propios favoritos
CREATE POLICY "Users can view own favorites" ON public.favorites FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own favorites" ON public.favorites FOR ALL USING (auth.uid() = user_id);

-- 7. Trigger (Disparador) automático para cuando alguien se registra con Google/Apple/Email
-- Esto hace que cada vez que alguien se crea una cuenta en Auth, se cree su perfil en `public.users` con 3 preguntas gratis.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, nombre, preguntas_restantes, is_premium)
  VALUES (new.id, new.email, new.raw_user_meta_data->>'full_name', 3, false);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
