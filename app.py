import streamlit as st
from PIL import Image, ImageDraw
import math
import random
from fpdf import FPDF
import io

# הגדרות דף
st.set_page_config(
    page_title="מחולל דאבל אישי - יצירת משחק קלפים בעיצוב שלך",
    page_icon="🎴",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': """
            ### מחולל דאבל אישי
            האתר הזה נוצר כדי לעזור לכם ליצור משחקי דאבל מותאמים אישית בקלות.
            פשוט מעלים תמונות, והאלגוריתם דואג לכל השאר!
        """
    }
)
# --- פונקציות עזר ---

def generate_dobble_indices(n):
    """אלגוריתם לייצור רשימת האינדקסים של המשחק"""
    cards = []
    for i in range(n + 1):
        cards.append([(i * n) + j for j in range(n)] + [n**2 + n])
    for i in range(n):
        for j in range(n):
            card = []
            for k in range(n):
                card.append(k * n + (i * k + j) % n)
            card.append(n**2 + i)
            cards.append(card)
    return cards

def export_to_pdf(card_images):
    """יצירת קובץ PDF עם קלפים בקוטר 8.5 ס"מ"""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(0)
    
    # הגדרות מידות (במילימטרים)
    card_size_mm = 85  # קוטר 8.5 ס"מ
    margin = 15        # שוליים מהצד
    spacing = 10       # רווח בין קלפים
    
    # נסדר 6 קלפים בדף (2 טורים, 3 שורות)
    for i in range(0, len(card_images), 6):
        pdf.add_page()
        
        for j in range(6):
            if i + j >= len(card_images):
                break
            
            # חישוב מיקום (טור ושורה)
            col = j % 2
            row = j // 2
            
            x_pos = margin + (col * (card_size_mm + spacing))
            y_pos = margin + (row * (card_size_mm + spacing))
            
            # שמירת התמונה לזיכרון והוספה ל-PDF
            img_buffer = io.BytesIO()
            card_images[i + j].save(img_buffer, format="PNG")
            pdf.image(img_buffer, x=x_pos, y=y_pos, w=card_size_mm)
            
    return bytes(pdf.output())
# --- ממשק האתר ---

st.title("🎴 יוצר קלפי דאבל מוכן להדפסה")

# הגדרות בצידי המסך
symbols_on_card = st.sidebar.selectbox("כמה סמלים על כל קלף?", [3, 4, 6, 8])
n = symbols_on_card - 1
total_needed = n**2 + n + 1

st.sidebar.info(f"עבור {symbols_on_card} סמלים, העלי {total_needed} תמונות.")

uploaded_files = st.file_uploader("העלי איורים", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

# --- שלב יצירת המשחק ---

if uploaded_files and len(uploaded_files) >= total_needed:
    st.success("יש מספיק תמונות! לחצי על הכפתור כדי לייצר את הקלפים.")
    
    if st.button("✨ צור משחק וקובץ להורדה"):
        # טעינת התמונות וחישוב האינדקסים בתוך הבלוק של הכפתור
        images = [Image.open(f).convert("RGBA") for f in uploaded_files[:total_needed]]
        deck_indices = generate_dobble_indices(n)
        
        all_cards_for_pdf = []
        st.divider()
        cols = st.columns(3)
        
        # יצירת הקלפים והצגתם
        for idx, card_indices in enumerate(deck_indices):
            # יצירת קנבס הקלף
            card_img = Image.new("RGBA", (500, 500), (255, 255, 255, 0))
            draw = ImageDraw.Draw(card_img)
            draw.ellipse([10, 10, 490, 490], fill="white", outline="black", width=3)
            
            # פיזור סמלים בתוך הקלף
            num_on_card = len(card_indices)
            for i, symbol_idx in enumerate(card_indices):
                symbol = images[symbol_idx].copy()
                
                # הקטנה יחסית של הסמלים כדי שלא יצאו מהמסגרת
                size = int(500 / (math.sqrt(num_on_card) + 1.8)) 
                symbol.thumbnail((size, size))
                
                # סיבוב התמונה
                symbol = symbol.rotate(random.randint(0, 360), expand=True, resample=Image.BICUBIC)
                
                # חישוב מיקום מעגלי - צמצמנו את הרדיוס ל-100 כדי למרכז יותר
                angle = (i / num_on_card) * 2 * math.pi
                radius = 100 
                
                # חישוב מרכז התמונה
                center_x = 250 + int(radius * math.cos(angle))
                center_y = 250 + int(radius * math.sin(angle))
                
                # חישוב הפינה (עבור paste) כך שהמרכז יהיה מדויק
                upper_left_x = center_x - (symbol.width // 2)
                upper_left_y = center_y - (symbol.height // 2)
                
                # הדבקה עם התחשבות בשקיפות
                card_img.paste(symbol, (upper_left_x, upper_left_y), symbol if symbol.mode == 'RGBA' else None)
            # שמירה לרשימת ה-PDF והצגה באתר
            all_cards_for_pdf.append(card_img)
            cols[idx % 3].image(card_img, use_container_width=True)
        
        # יצירת כפתור ההורדה - רק אחרי שהלולאה נגמרה והרשימה מלאה
        st.divider()
        pdf_bytes = export_to_pdf(all_cards_for_pdf)
        st.download_button(
            label="📥 הורדת כל הקלפים ב-PDF",
            data=pdf_bytes,
            file_name="my_dobble_game.pdf",
            mime="application/pdf"
        )
else:
    if uploaded_files:
        st.warning(f"חסרות עוד {total_needed - len(uploaded_files)} תמונות.")

st.markdown("---")
st.markdown("""
### איך עובד מחולל הדאבל?
המשחק מבוסס על עקרונות מתמטיים של **מישור פרויקטיבי סופי**. 
כל שני קלפים במשחק מכילים בדיוק תמונה אחת משותפת. 
זהו כלי נהדר ליצירת מתנות אישיות, משחקים לימי הולדת או עזרי למידה בגני ילדים ובבתי ספר.
""")