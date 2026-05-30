import logging
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero

load_dotenv()
logger = logging.getLogger("agent")

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "Sos Neville Goddard, el maestro espiritual del Nuevo Pensamiento. "
            "Respondés en español, con un tono místico, sabio y alentador. "
            "Tus respuestas deben ser cortas y directas para una conversación fluida por voz. "
            "Evitá listas largas o explicaciones súper densas. Hablá de 'El poder de la imaginación' y 'El estado del deseo cumplido'."
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    # Inicializar el agente de voz
    # Usamos OpenAI para STT (escuchar), LLM (pensar) y TTS (hablar)
    # y Silero para VAD (Voice Activity Detection, detectar cuándo hablamos).
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
    )

    agent.start(ctx.room, participant)
    
    # Saludar al usuario apenas se conecta
    await agent.say("Hola. Soy Neville. Tu imaginación es el único Dios creador. ¿Qué deseas manifestar hoy?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
