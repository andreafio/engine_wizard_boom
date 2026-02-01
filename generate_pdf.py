"""
Generate PDF presentation from test output
"""
from fpdf import FPDF
from datetime import datetime

class PresentationPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'Wizard BOOM Engine - Marketing Strategy', 0, 1, 'R')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 18)
        self.set_text_color(33, 37, 41)
        self.cell(0, 12, title, 0, 1, 'L')
        self.ln(4)
    
    def bullet_point(self, text):
        self.set_font('Arial', '', 11)
        self.set_text_color(52, 58, 64)
        # Bullet symbol with proper spacing
        self.set_x(self.l_margin + 5)
        self.cell(5, 7, '-', 0, 0)
        # Text with wrapping
        self.set_x(self.l_margin + 12)
        current_y = self.get_y()
        self.multi_cell(0, 7, text)
        self.ln(2)
    
    def section_text(self, text):
        self.set_font('Arial', '', 11)
        self.set_text_color(52, 58, 64)
        self.multi_cell(0, 7, text)
        self.ln(3)

def create_presentation_pdf():
    pdf = PresentationPDF()
    
    # Cover page
    pdf.add_page()
    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(13, 110, 253)
    pdf.ln(60)
    pdf.cell(0, 15, 'Marketing Strategy', 0, 1, 'C')
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(108, 117, 125)
    pdf.cell(0, 12, 'B2B SaaS Lead Generation', 0, 1, 'C')
    pdf.ln(20)
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f'Generato: {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
    pdf.cell(0, 8, 'Obiettivo: 100 lead qualificati/mese', 0, 1, 'C')
    
    # Slide 1: Contesto Aziendale
    pdf.add_page()
    pdf.chapter_title('[1] Contesto Aziendale')
    pdf.bullet_point('Settore: B2B SaaS con modello di business in abbonamento')
    pdf.bullet_point('Dimensione azienda: Startup con 10-50 dipendenti')
    pdf.bullet_point('Focalizzazione: Automazione marketing')
    
    # Slide 2: Obiettivo Strategico
    pdf.add_page()
    pdf.chapter_title('[2] Obiettivo Strategico')
    pdf.bullet_point('Goal primario: Generare lead qualificati')
    pdf.bullet_point('Obiettivo: 100 lead al mese')
    pdf.bullet_point('Strategia: Focalizzata sulla lead generation')
    
    # Slide 3: Target Market
    pdf.add_page()
    pdf.chapter_title('[3] Target Market')
    pdf.bullet_point('Ruolo target: Marketing Manager')
    pdf.bullet_point('Ambito geografico: Italia')
    pdf.bullet_point('Focus: Aziende B2B nel settore tech')
    
    # Slide 4: Value Proposition
    pdf.add_page()
    pdf.chapter_title('[4] Value Proposition')
    pdf.bullet_point('Offerta: Piattaforma software per automazione')
    pdf.bullet_point('Problema chiave: Automazione processi marketing manuali')
    pdf.bullet_point('Differenziazione: Automazione AI e analytics integrati')
    
    # Slide 5: Canali & Asset
    pdf.add_page()
    pdf.chapter_title('[5] Canali & Asset')
    pdf.bullet_point('Canali selezionati: LinkedIn, Google Ads, Content Marketing')
    pdf.bullet_point('Asset disponibili: Sito web, landing pages, case studies')
    pdf.bullet_point('Note: Nessuna nota aggiuntiva sugli asset')
    
    # Slide 6: Vincoli Operativi
    pdf.add_page()
    pdf.chapter_title('[6] Vincoli Operativi')
    pdf.bullet_point('Budget: 5.000-10.000 euro/mese')
    pdf.bullet_point('Timing previsto: Q1 2026')
    pdf.bullet_point('Team: Marketing interno composto da 2 persone')
    
    # Report Section
    pdf.add_page()
    pdf.chapter_title('Report Strategico')
    
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(13, 110, 253)
    pdf.cell(0, 10, 'Executive Summary', 0, 1)
    pdf.section_text('Il progetto mira a generare 100 lead qualificati al mese nel settore B2B SaaS. La strategia si basa su canali digitali mirati e una proposta di valore differenziante.')
    
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(13, 110, 253)
    pdf.cell(0, 10, 'Contesto Strategico', 0, 1)
    pdf.section_text("L'azienda opera nel settore B2B SaaS, con un modello di abbonamento. La dimensione ridotta consente flessibilità, ma richiede attenzione ai costi e all'efficienza.")
    
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(13, 110, 253)
    pdf.cell(0, 10, 'Key Insights', 0, 1)
    pdf.section_text("Il target principale sono i Marketing Manager in Italia. La proposta di valore si distingue per l'uso di AI nell'automazione, risolvendo problemi di efficienza.")
    
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(13, 110, 253)
    pdf.cell(0, 10, 'Azioni Raccomandate', 0, 1)
    pdf.bullet_point('Sviluppare contenuti mirati per LinkedIn e Google Ads')
    pdf.bullet_point('Ottimizzare le landing pages per la conversione')
    pdf.bullet_point('Monitorare i lead generati mensilmente')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(13, 110, 253)
    pdf.cell(0, 10, 'Rischi & Assunzioni', 0, 1)
    pdf.section_text('Rischi: Budget limitato e capacità del team ridotta')
    pdf.section_text('Assunzioni: Efficacia dei canali scelti e interesse del target per offerta')
    
    # Assumptions
    pdf.add_page()
    pdf.chapter_title('Assumptions')
    pdf.set_fill_color(255, 243, 205)
    pdf.set_font('Arial', 'I', 11)
    pdf.set_text_color(133, 100, 4)
    pdf.multi_cell(0, 8, 'Mancano dati quantitativi (CPL, CAC, conversioni, ROI): le priorita sono qualitative.', 0, 'L', True)
    
    # Next Steps
    pdf.ln(10)
    pdf.chapter_title('Next Steps')
    pdf.bullet_point('Definire il piano di contenuti per i canali selezionati')
    pdf.bullet_point('Stabilire un calendario per la campagna di lead generation')
    pdf.bullet_point('Monitorare e analizzare i risultati mensili')
    
    # Save PDF
    output_file = 'presentation_output.pdf'
    pdf.output(output_file)
    print(f'✅ PDF generato con successo: {output_file}')
    return output_file

if __name__ == '__main__':
    create_presentation_pdf()
