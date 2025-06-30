import streamlit as st
import requests
import urllib.parse
import time
from PIL import Image

# Handle pytesseract import with fallback
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    st.warning("⚠️ OCR functionality is currently unavailable.")

# Page configuration
st.set_page_config(
    page_title="Universal Language Translator",
    page_icon="🌐",
    layout="wide"
)

class UniversalTranslator:
    def __init__(self):
        self.lingva_instances = [
            "https://lingva.ml/api/v1",
            "https://translate.igodo.eu/api/v1",
            "https://translate.plausibility.cloud/api/v1"
        ]
        self.current_instance = 0
        
        self.languages = {
            'auto': 'Auto-detect', 'en': 'English', 'hi': 'Hindi', 'te': 'Telugu',
            'ta': 'Tamil', 'kn': 'Kannada', 'ml': 'Malayalam', 'mr': 'Marathi',
            'bn': 'Bengali', 'gu': 'Gujarati', 'pa': 'Punjabi', 'or': 'Odia',
            'as': 'Assamese', 'ur': 'Urdu', 'ne': 'Nepali', 'si': 'Sinhala',
            'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian',
            'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese', 'ko': 'Korean',
            'zh': 'Chinese', 'ar': 'Arabic', 'tr': 'Turkish', 'nl': 'Dutch',
            'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian', 'fi': 'Finnish'
        }

    def translate_text(self, text, source_lang='auto', target_lang='en'):
        """Core translation function with fallback support"""
        if not text or not text.strip():
            return "No text to translate"
        
        # If source and target are the same, return original
        if source_lang == target_lang and source_lang != 'auto':
            return text
            
        for attempt in range(len(self.lingva_instances)):
            try:
                base_url = self.lingva_instances[self.current_instance]
                text_chunk = text.strip()[:1000]  # Limit chunk size
                encoded_text = urllib.parse.quote(text_chunk)
                
                url = f"{base_url}/{source_lang}/{target_lang}/{encoded_text}"
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                translation = data.get('translation', '').strip()
                
                if translation and translation != text_chunk:
                    return translation
                elif translation:
                    return translation
                    
            except Exception as e:
                self.current_instance = (self.current_instance + 1) % len(self.lingva_instances)
                if attempt < len(self.lingva_instances) - 1:
                    time.sleep(1)
        
        return f"Translation unavailable. Original: {text[:200]}{'...' if len(text) > 200 else ''}"

    def translate_long_content(self, text, target_lang, source_lang='auto', chunk_size=700):
        """Translate long content by intelligent chunking"""
        if not text or not text.strip():
            return "No content to translate"
        
        # If target is English and source is auto, and text appears to be English, return as is
        if target_lang == 'en' and source_lang == 'auto' and self._is_likely_english(text):
            return text
        
        if len(text) <= chunk_size:
            return self.translate_text(text, source_lang, target_lang)
        
        # Smart sentence splitting
        sentences = self._smart_sentence_split(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + " " + sentence) < chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Show progress for long translations
        if len(chunks) > 3:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        translated_chunks = []
        
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                if len(chunks) > 3:
                    status_text.text(f"Translating chunk {i+1} of {len(chunks)}...")
                
                translated_chunk = self.translate_text(chunk, source_lang, target_lang)
                translated_chunks.append(translated_chunk)
                
                if len(chunks) > 3:
                    progress_bar.progress((i + 1) / len(chunks))
                    time.sleep(0.3)  # Rate limiting
        
        if len(chunks) > 3:
            progress_bar.empty()
            status_text.empty()
        
        return ' '.join(translated_chunks)

    def _smart_sentence_split(self, text):
        """Intelligent sentence splitting"""
        # Replace sentence endings with temporary markers
        text = text.replace('. ', '.|SPLIT|')
        text = text.replace('! ', '!|SPLIT|')
        text = text.replace('? ', '?|SPLIT|')
        text = text.replace('.\n', '.|SPLIT|')
        text = text.replace('!\n', '!|SPLIT|')
        text = text.replace('?\n', '?|SPLIT|')
        
        sentences = [s.strip() for s in text.split('|SPLIT|') if s.strip()]
        return sentences

    def _is_likely_english(self, text):
        """Simple heuristic to detect if text is likely English"""
        english_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with', 'for', 'as', 'was', 'on', 'are']
        words = text.lower().split()[:50]  # Check first 50 words
        english_count = sum(1 for word in words if word in english_words)
        return english_count > len(words) * 0.1  # If >10% are common English words

    def extract_text_from_image(self, image):
        """Extract text from uploaded image using OCR"""
        if not OCR_AVAILABLE:
            return "OCR functionality is not available. Please install pytesseract."
        
        try:
            if hasattr(image, 'read'):
                image = Image.open(image)
            
            # Configure tesseract for better accuracy
            custom_config = r'--oem 3 --psm 6'
            extracted_text = pytesseract.image_to_string(image, config=custom_config)
            return extracted_text.strip()
            
        except Exception as e:
            st.error(f"OCR Error: {str(e)}")
            return ""

    def fetch_wikipedia_article(self, title):
        """Fetch Wikipedia article content"""
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "prop": "extracts",
                "explaintext": True,
                "titles": title,
                "format": "json",
                "exintro": False,  # Get full article, not just intro
                "exsectionformat": "plain"
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            pages = data['query']['pages']
            
            if pages:
                page = next(iter(pages.values()))
                
                if 'missing' in page:
                    return None
                
                if 'extract' in page and page['extract']:
                    # Limit content for better performance
                    content = page['extract']
                    if len(content) > 4000:
                        content = content[:4000] + "... [Content truncated for translation]"
                    
                    return {
                        'title': page.get('title', title),
                        'content': content,
                        'source': 'Wikipedia English',
                        'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    }
            
            return None
            
        except Exception as e:
            st.error(f"Wikipedia fetch error: {str(e)}")
            return None

# Initialize translator
@st.cache_resource
def get_translator():
    return UniversalTranslator()

translator = get_translator()

def main():
    st.title("🌐 Universal Language Translator")
    st.markdown("*Translate text, images, and Wikipedia articles into 25+ languages including major Indic languages*")
    
    # Show OCR status
    if not OCR_AVAILABLE:
        st.error("🔧 **Setup Required**: OCR functionality is disabled. Please add the required configuration files to enable image translation.")
        with st.expander("📋 Setup Instructions"):
            st.markdown("""
            To enable OCR (image text extraction), you need to:
            
            1. **Create `requirements.txt`** in your project root:
            ```
            streamlit>=1.28.0
            requests>=2.25.1
            Pillow>=8.3.2
            pytesseract>=0.3.8
            urllib3>=1.26.0
            ```
            
            2. **Create `packages.txt`** in your project root:
            ```
            tesseract-ocr
            tesseract-ocr-eng
            tesseract-ocr-hin
            tesseract-ocr-tam
            tesseract-ocr-tel
            tesseract-ocr-kan
            tesseract-ocr-mal
            tesseract-ocr-mar
            tesseract-ocr-ben
            tesseract-ocr-guj
            tesseract-ocr-pan
            tesseract-ocr-ori
            ```
            
            3. **Redeploy your app** on Streamlit Cloud
            """)
    
    # Language selection in sidebar
    with st.sidebar:
        st.header("🎯 Translation Settings")
        
        source_lang = st.selectbox(
            "📥 Source Language",
            options=list(translator.languages.keys()),
            format_func=lambda x: translator.languages[x],
            index=0,  # Auto-detect by default
            help="Select source language or use auto-detect"
        )
        
        target_lang = st.selectbox(
            "📤 Target Language",
            options=[k for k in translator.languages.keys() if k != 'auto'],
            format_func=lambda x: translator.languages[x],
            index=0,  # English by default
            help="Select the language you want to translate to"
        )
        
        st.info(f"*Translating:* {translator.languages[source_lang]} → {translator.languages[target_lang]}")
        
        # Language info
        st.markdown("### 🇮🇳 Supported Indic Languages")
        indic_langs = ['Hindi', 'Telugu', 'Tamil', 'Kannada', 'Malayalam', 'Marathi', 'Bengali', 'Gujarati']
        for lang in indic_langs:
            st.markdown(f"• {lang}")

    # Main content area - only show available tabs
    if OCR_AVAILABLE:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Text Translation", 
            "🖼 Image Translation", 
            "📚 Wikipedia Translation", 
            "⚡ Quick Translate"
        ])
    else:
        tab1, tab3, tab4 = st.tabs([
            "📝 Text Translation", 
            "📚 Wikipedia Translation", 
            "⚡ Quick Translate"
        ])

    # Tab 1: Text Translation
    with tab1:
        st.header("📝 Text Translation")
        st.markdown("Enter any text to translate it into your target language")
        
        text_input = st.text_area(
            "Enter text to translate:",
            height=200,
            placeholder="Type or paste your text here...",
            help="Supports long texts - they will be automatically split into chunks for translation"
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔄 Translate Text", type="primary", use_container_width=True):
                if text_input.strip():
                    with st.spinner(f"Translating to {translator.languages[target_lang]}..."):
                        translation = translator.translate_long_content(text_input, target_lang, source_lang)
                    
                    st.success("✅ Translation Complete!")
                    st.markdown("### 📄 Translated Text")
                    st.markdown(translation)
                    
                    # Copy-friendly format
                    st.markdown("### 📋 Copy Text")
                    st.code(translation, language=None)
                else:
                    st.warning("⚠ Please enter some text to translate")
        
        with col2:
            if st.button("🗑 Clear", use_container_width=True):
                st.rerun()

    # Tab 2: Image Translation (only if OCR is available)
    if OCR_AVAILABLE:
        with tab2:
            st.header("🖼 Image Text Translation")
            st.markdown("Upload an image with text to extract and translate it")
            
            uploaded_file = st.file_uploader(
                "Choose an image file",
                type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
                help="Upload images containing text (documents, signs, screenshots, etc.)"
            )
            
            if uploaded_file is not None:
                # Display image
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🖼 Uploaded Image")
                    st.image(uploaded_file, caption="Your uploaded image", use_column_width=True)
                
                with col2:
                    st.markdown("#### 🔧 Actions")
                    
                    if st.button("🔍 Extract & Translate", type="primary", use_container_width=True):
                        with st.spinner("🔍 Extracting text from image..."):
                            extracted_text = translator.extract_text_from_image(uploaded_file)
                        
                        if extracted_text:
                            st.markdown("#### 📝 Extracted Text")
                            st.text_area("", value=extracted_text, height=150, disabled=True)
                            
                            # Always translate unless target is English and text appears to be English
                            with st.spinner(f"🔄 Translating to {translator.languages[target_lang]}..."):
                                translation = translator.translate_long_content(extracted_text, target_lang, source_lang)
                            
                            st.markdown("#### 🌐 Translation")
                            st.success(translation)
                            
                            # Copy format
                            st.code(translation, language=None)
                        else:
                            st.error("❌ No readable text found in the image")
                    
                    if st.button("📝 Extract Text Only", use_container_width=True):
                        with st.spinner("🔍 Extracting text..."):
                            extracted_text = translator.extract_text_from_image(uploaded_file)
                        
                        if extracted_text:
                            st.markdown("#### 📝 Extracted Text")
                            st.text_area("", value=extracted_text, height=200, disabled=True)
                        else:
                            st.error("❌ No readable text found in the image")

    # Tab 3: Wikipedia Translation
    with tab3:
        st.header("📚 Wikipedia Article Translation")
        st.markdown("Search Wikipedia articles and translate them into any language")
        
        search_term = st.text_input(
            "🔍 Search Wikipedia:",
            placeholder="Enter topic name (e.g., 'India', 'Technology', 'Albert Einstein')",
            help="Enter any topic to search for on Wikipedia"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🔍 Search & Translate", type="primary", use_container_width=True):
                if search_term.strip():
                    with st.spinner("🔍 Searching Wikipedia..."):
                        article = translator.fetch_wikipedia_article(search_term)
                    
                    if article:
                        st.success(f"✅ Found article: *{article['title']}*")
                        st.markdown(f"📖 Source: [{article['source']}]({article['url']})")
                        
                        # Show original article in expander
                        with st.expander("📄 Original Article (English)", expanded=False):
                            st.markdown(article['content'])
                        
                        # Always translate the Wikipedia content
                        st.markdown(f"### 🌐 Article in {translator.languages[target_lang]}")
                        
                        with st.spinner(f"🔄 Translating article to {translator.languages[target_lang]}..."):
                            translated_content = translator.translate_long_content(
                                article['content'], 
                                target_lang, 
                                'en'  # Wikipedia content is in English
                            )
                        
                        st.markdown("#### 📖 Translated Article")
                        st.markdown(translated_content)
                        
                        # Copy format
                        with st.expander("📋 Copy Translated Text"):
                            st.code(translated_content, language=None)
                            
                    else:
                        st.error(f"❌ No Wikipedia article found for '{search_term}'. Try a different search term.")
                else:
                    st.warning("⚠ Please enter a search term")
        
        with col2:
            if st.button("🔍 Search Only", use_container_width=True):
                if search_term.strip():
                    with st.spinner("🔍 Searching..."):
                        article = translator.fetch_wikipedia_article(search_term)
                    
                    if article:
                        st.success(f"✅ Found: *{article['title']}*")
                        st.markdown(article['content'][:500] + "...")
                        st.markdown(f"[Read full article]({article['url']})")

    # Tab 4: Quick Translation
    with tab4:
        st.header("⚡ Quick Translation")
        st.markdown("Instant translation for short texts and phrases")
        
        quick_text = st.text_input(
            "Enter text for quick translation:",
            placeholder="Type a word, phrase, or sentence...",
            help="Perfect for quick translations of short texts"
        )
        
        if st.button("⚡ Quick Translate", type="primary", use_container_width=True):
            if quick_text.strip():
                with st.spinner("⚡ Translating..."):
                    translation = translator.translate_text(quick_text, source_lang, target_lang)
                
                # Side by side display
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📥 Original")
                    st.info(quick_text)
                
                with col2:
                    st.markdown(f"#### 📤 {translator.languages[target_lang]}")
                    st.success(translation)
            else:
                st.warning("⚠ Please enter some text to translate")

    # Footer
    st.markdown("---")
    
    # Clean footer without HTML tags
    footer_text = "🌐 Universal Language Translator | 📚 Wikipedia Integration"
    if OCR_AVAILABLE:
        footer_text += " | 🖼 Image OCR"
    footer_text += " | 25+ Languages Supported"
    
    st.markdown(f"**{footer_text}**")
    st.markdown("*Bridging language barriers with AI-powered translation*")

if __name__ == "__main__":
    main()
