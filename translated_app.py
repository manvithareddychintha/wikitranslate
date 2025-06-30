# Footer
st.markdown("---")
footer_content = """
    **🌐 Universal Language Translator** | 
    **📚 Wikipedia Integration** | 
    {image_ocr}**25+ Languages Supported**  
    *Bridging language barriers with AI-powered translation*
""".format(
    image_ocr="**🖼 Image OCR** | " if OCR_AVAILABLE else ""
)
st.markdown(footer_content)
