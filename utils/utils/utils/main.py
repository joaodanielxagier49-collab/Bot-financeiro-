from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import io
import os
import logging
from flask import Flask

# Importar módulos próprios
from utils.image_processor import ImageProcessor
from utils.audio_processor import AudioProcessor
from utils.categorizer import FinancialCategorizer

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inicializar processadores
image_processor = ImageProcessor()
audio_processor = AudioProcessor()
categorizer = FinancialCategorizer()

# Configurações
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PORT = int(os.getenv('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Flask app para Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Financial Bot está rodando!"

# Comandos do bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
    🤖 *Bot Financeiro Pessoal*
    
    Eu ajudo você a organizar suas finanças! Envie:
    
    📷 *Imagens* de comprovantes ou notas fiscais
    🎤 *Áudios* descrevendo suas transações
    💬 *Mensagens* de texto com valores gastos/recebidos
    
    Exemplos:
    - "Gastei R$ 80,00 no churrasco"
    - "Recebi R$ 1.500,00 de freelance"
    - Imagem de um comprovante de salário
    
    Vou categorizar automaticamente suas transações!
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    📋 *Como usar:*
    
    1. *Envie uma imagem* com texto legível
    2. *Grave um áudio* descrevendo a transação
    3. *Digite* diretamente:
       "Gastei R$ 50,00 na farmácia"
       "Recebi R$ 2.000,00 de salário"
    
    🏷️ *Categorias automáticas:*
    Alimentação, Saúde, Transporte, Lazer, Moradia, Educação, Vestuário, Salário, Freelance, etc.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("📷 Processando imagem...")
        
        # Baixar imagem
        photo_file = await update.message.photo[-1].get_file()
        photo_io = io.BytesIO()
        await photo_file.download_to_memory(photo_io)
        photo_io.seek(0)
        
        # Abrir imagem
        image = Image.open(photo_io)
        
        # Extrair texto
        extracted_text = image_processor.extract_text_from_image(image)
        
        if not extracted_text:
            await update.message.reply_text("❌ Não consegui ler texto na imagem. Tente uma foto mais nítida.")
            return
        
        # Processar dados financeiros
        financial_data = categorizer.extract_financial_data(extracted_text)
        
        # Responder com resumo
        response = format_financial_response(financial_data, extracted_text)
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erro no processamento de imagem: {e}")
        await update.message.reply_text("❌ Erro ao processar imagem. Tente novamente.")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🎤 Processando áudio...")
        
        # Baixar áudio
        audio_file = await update.message.voice.get_file()
        audio_io = io.BytesIO()
        await audio_file.download_to_memory(audio_io)
        audio_data = audio_io.getvalue()
        
        # Converter speech para texto
        transcribed_text = audio_processor.speech_to_text(audio_data)
        
        if not transcribed_text:
            await update.message.reply_text("❌ Não consegui entender o áudio. Tente novamente.")
            return
        
        # Processar dados financeiros
        financial_data = categorizer.extract_financial_data(transcribed_text)
        financial_data['descricao'] = transcribed_text
        
        # Responder com resumo
        response = format_financial_response(financial_data, transcribed_text)
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erro no processamento de áudio: {e}")
        await update.message.reply_text("❌ Erro ao processar áudio. Tente novamente.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        
        # Processar dados financeiros
        financial_data = categorizer.extract_financial_data(text)
        
        if not financial_data['tipo']:
            # Tentar inferir pelo contexto
            if any(word in text.lower() for word in ['gastei', 'paguei', 'comprei', 'comprar']):
                financial_data['tipo'] = 'Despesa'
            elif any(word in text.lower() for word in ['recebi', 'ganhei', 'salário', 'pagamento']):
                financial_data['tipo'] = 'Receita'
        
        # Se não tem descrição, usar o texto completo
        if not financial_data['descricao']:
            financial_data['descricao'] = text
        
        # Categorizar
        financial_data['categoria'] = categorizer.categorize_transaction(
            financial_data['descricao'], financial_data['tipo'] or 'Despesa'
        )
        
        # Responder com resumo
        response = format_financial_response(financial_data, text)
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erro no processamento de texto: {e}")
        await update.message.reply_text("❌ Erro ao processar mensagem. Tente novamente.")

def format_financial_response(financial_data, original_text=None):
    """Formata resposta bonita para o usuário"""
    
    emoji = "💸" if financial_data['tipo'] == 'Despesa' else "💰"
    
    response = f"""
{emoji} *Transação Processada*

📝 *Descrição:* {financial_data['descricao']}
🏷️ *Tipo:* {financial_data['tipo'] or 'Não identificado'}
💵 *Valor:* R$ {financial_data['valor']:,.2f if financial_data['valor'] else 'N/A'}
📂 *Categoria:* {financial_data['categoria'] or 'Não categorizada'}
📅 *Data:* {financial_data['data'] or 'Data atual'}
"""
    
    if original_text and len(original_text) < 100:
        response += f"\n_Texto detectado: {original_text}_"
    
    return response

def main():
    """Inicializa o bot"""
    if not TOKEN:
        logger.error("TOKEN não encontrado!")
        return
    
    # Criar application
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VOICE, handle_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Iniciar bot
    if WEBHOOK_URL:
        # Para produção com webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
    else:
        # Para desenvolvimento
        application.run_polling()

if __name__ == '__main__':
    main()
