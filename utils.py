
import streamlit as st
import streamlit.components.v1 as components
from config import CONFETTI_CSS

def show_confetti():
    """Displays a confetti animation in the Streamlit app."""
    st.markdown(CONFETTI_CSS, unsafe_allow_html=True)
    confetti_js = """
    <script>
    function createConfetti() {
        const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff'];
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            document.body.appendChild(confetti);
            setTimeout(() => confetti.remove(), 3000);
        }
    }
    createConfetti();
    </script>
    """
    components.html(confetti_js, height=0)
