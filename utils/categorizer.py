import re
from datetime import datetime

class FinancialCategorizer:
    def __init__(self):
        self.categories = {
            'alimentação': ['mercado', 'supermercado', 'padaria', 'restaurante', 'lanche', 'comida', 'alimento', 'bebidas', 'churrasco'],
            'saúde': ['farmácia', 'drogaria', 'medicamento', 'remédio', 'consulta', 'médico', 'hospital', 'saúde'],
            'transporte': ['combustível', 'gasolina', 'ônibus', 'metrô', 'táxi', 'uber', 'transporte', 'estacionamento'],
            'lazer': ['cinema', 'shopping', 'parque', 'viagem', 'hotel', 'lazer', 'entretenimento', 'festas'],
            'moradia': ['aluguel', 'condomínio', 'luz', 'água', 'gás', 'internet', 'telefone', 'manutenção'],
            'educação': ['curso', 'livro', 'material', 'escola', 'faculdade', 'universidade', 'educação'],
            'vestuário': ['roupa', 'calçado', 'acessório', 'loja', 'shopping'],
            'salário': ['salário', 'ordenado', 'contracheque', 'pagamento'],
            'freelance': ['freelance', 'projeto', 'serviço', 'consultoria'],
            'investimentos': ['investimento', 'ações', 'bolsa', 'poupança', 'tesouro'],
            'outros': ['diversos', 'outros', 'variados']
        }
    
    def categorize_transaction(self, description, transaction_type):
        description_lower = description.lower()
        
        # Se for receita, categorias específicas
        if transaction_type.lower() == 'receita':
            if any(word in description_lower for word in self.categories['salário']):
                return 'Salário'
            elif any(word in description_lower for word in self.categories['freelance']):
                return 'Freelance'
            elif any(word in description_lower for word in self.categories['investimentos']):
                return 'Investimentos'
            else:
                return 'Outras Receitas'
        
        # Para despesas
        for category, keywords in self.categories.items():
            if category not in ['salário', 'freelance', 'investimentos']:
                if any(keyword in description_lower for keyword in keywords):
                    return category.title()
        
        return 'Outros'
    
    def extract_financial_data(self, text):
        data = {
            'tipo': None,
            'descricao': '',
            'valor': None,
            'categoria': None,
            'data': None
        }
        
        # Extrair tipo (Receita/Despesa)
        if 'tipo: receita' in text.lower() or 'recebi' in text.lower():
            data['tipo'] = 'Receita'
        elif 'tipo: despesa' in text.lower() or 'gastei' in text.lower():
            data['tipo'] = 'Despesa'
        
        # Extrair valor
        valor_pattern = r'R\$\s*([0-9.,]+)'
        valores = re.findall(valor_pattern, text)
        if valores:
            # Pegar o maior valor (geralmente é o principal)
            valores_limpos = [float(v.replace('.', '').replace(',', '.')) for v in valores if v]
            if valores_limpos:
                data['valor'] = max(valores_limpos)
        
        # Extrair descrição
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'descrição:' in line.lower():
                data['descricao'] = line.split(':', 1)[1].strip()
            elif 'recebi' in line.lower() and 'descrição' not in text.lower():
                data['descricao'] = line.strip()
            elif 'gastei' in line.lower():
                data['descricao'] = line.strip()
        
        # Extrair data
        data_pattern = r'(\d{2}/\d{2}/\d{4})'
        datas = re.findall(data_pattern, text)
        if datas:
            data['data'] = datas[0]
        else:
            data['data'] = datetime.now().strftime('%d/%m/%Y')
        
        # Categorizar automaticamente
        if data['descricao'] and data['tipo']:
            data['categoria'] = self.categorize_transaction(data['descricao'], data['tipo'])
        
        return data
