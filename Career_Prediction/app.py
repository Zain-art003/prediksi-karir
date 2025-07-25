import streamlit as st
import random
import pandas as pd
import joblib          
import numpy as np      
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'quiz_results' not in st.session_state:
    st.session_state.quiz_results = {}
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

def back_home():
    st.session_state.page = 'home'

def calculate_score(answers, selected_questions=None, scoring_type='percentage'):
    """Calculate quiz score based on answers"""
    if not answers or not selected_questions:
        return 0
    
    if scoring_type == 'percentage_correct': # New scoring type for quizzes with explicit correct answers
        correct_answers_count = 0
        for i, answer_index in enumerate(answers):
            if 'correct' in selected_questions[i] and answer_index == selected_questions[i]['correct']:
                correct_answers_count += 1
        return (correct_answers_count / len(selected_questions)) * 100
    
    elif scoring_type == 'weighted':
        # Weight answers based on quality (first option = 100%, second = 50%, third = 25%)
        # This assumes the first option is always the "best" for SJT/Soft Skills
        total_score = 0
        for answer_index in answers:
            if answer_index == 0:  # First option
                total_score += 100
            elif answer_index == 1:  # Second option
                total_score += 50
            elif answer_index == 2:  # Third option
                total_score += 25
        return total_score / len(answers)
    else:
        return 0 # Default to 0 if scoring_type is not recognized

def predict_career(sjt_score, personality_score, tech_score, soft_score):
    """Predict career using KNN model"""
    try:
        # Load model artifacts
        knn = joblib.load("knn_model.joblib")
        le = joblib.load("label_encoder.joblib")
        scaler = joblib.load("scaler.joblib")
        
        # Prepare features (sesuaikan urutan dengan training data)
        # Ensure the order of features matches the training data: tech_score, soft_score, sjt_score, personality_score
        features = np.array([[tech_score, soft_score, sjt_score, personality_score]])
        features_scaled = scaler.transform(features)
        
        # Predict using KNN
        prediction = knn.predict(features_scaled)
        career = le.inverse_transform(prediction)[0]
        
        return career
        
    except FileNotFoundError:
        # Fallback to original rule-based prediction if model files not found
        st.warning("Model KNN tidak ditemukan, menggunakan prediksi berbasis aturan")
        return predict_career_fallback(sjt_score, personality_score, tech_score, soft_score)
    except Exception as e:
        st.error(f"Error dalam prediksi KNN: {str(e)}")
        return predict_career_fallback(sjt_score, personality_score, tech_score, soft_score)

def predict_career_fallback(sjt_score, personality_score, tech_score, soft_score):
    """Fallback prediction using original rule-based approach for 5 careers"""
    # Prioritize Tech Lead/Senior Developer
    if tech_score > 75 and soft_score > 65 and sjt_score > 70:
        return "Tech Lead / Senior Developer"
    # Then Software Developer
    elif tech_score > 70 and personality_score > 50:
        return "Software Developer"
    # Then Project Manager
    elif soft_score > 80 and sjt_score > 75:
        return "Project Manager"
    # Then Technical Specialist
    elif tech_score > 85:
        return "Technical Specialist"
    # Finally Business Analyst
    elif sjt_score > 70 and soft_score > 60:
        return "Business Analyst"
    else: # Default for other combinations within the 5 careers
        # This fallback might need fine-tuning based on your desired behavior
        # and how scores interact for these 5 specific roles.
        # For simplicity, if scores are lower across the board, default to a general tech role
        if tech_score > soft_score:
            return "Software Developer"
        else:
            return "Business Analyst"


def show_model_evaluation():
    """Display model evaluation metrics"""
    try:
        with open("models/model_evaluation_detailed.txt", "r") as f: # <--- Baris yang sudah diperbaiki
            metrics = f.read()
        st.text(metrics)
    except FileNotFoundError:
        st.info("File evaluasi model tidak ditemukan. Pastikan train_knn_model.py sudah dijalankan.") # Pesan lebih informatif
    except Exception as e:
        st.error(f"Error saat menampilkan evaluasi model: {str(e)}")

def get_career_recommendations(predicted_career, scores):
    """Get personalized career recommendations"""
    recommendations = {
        "Tech Lead / Senior Developer": {
            "strengths": ["Strong technical skills", "Good leadership potential", "Problem-solving abilities"],
            "areas_to_improve": ["Advanced team management", "Strategic technical vision"],
            "suggested_actions": ["Take advanced leadership courses", "Contribute to open-source projects", "Mentor junior developers"]
        },
        "Software Developer": {
            "strengths": ["Technical competency", "Logical thinking", "Problem-solving", "Code implementation"],
            "areas_to_improve": ["System design", "Code optimization", "Collaboration with non-technical teams"],
            "suggested_actions": ["Deepen knowledge in specific frameworks", "Practice algorithmic problem-solving", "Contribute to team design discussions"]
        },
        "Project Manager": {
            "strengths": ["Leadership abilities", "Communication skills", "Strategic thinking", "Organizational skills"],
            "areas_to_improve": ["Technical understanding of software development lifecycle", "Risk management in agile environments"],
            "suggested_actions": ["Learn agile methodologies deeply", "Take project management certifications (PMP/Scrum)", "Improve stakeholder management"]
        },
        "Technical Specialist": {
            "strengths": ["Deep technical knowledge in a specific area", "Problem-solving for complex technical issues", "Innovation in specialized fields"],
            "areas_to_improve": ["Cross-functional communication", "Broader business context understanding"],
            "suggested_actions": ["Specialize further in a niche technology (e.g., AI/ML, Cloud Security)", "Publish technical articles or give presentations", "Attend expert-level workshops"]
        },
        "Business Analyst": {
            "strengths": ["Analytical thinking", "Problem-solving", "Communication (bridging technical and business needs)", "Requirements gathering"],
            "areas_to_improve": ["Technical depth in software architecture", "Data modeling and advanced analysis"],
            "suggested_actions": ["Learn basic SQL/Python for data manipulation", "Study software development methodologies (e.g., Agile, Waterfall)", "Improve documentation and visualization skills"]
        }
    }
    
    return recommendations.get(predicted_career, {
        "strengths": ["Good foundation across areas"],
        "areas_to_improve": ["Specialized skills"],
        "suggested_actions": ["Identify specific interests", "Take skill assessments", "Explore various fields"]
    })

def display_results():
    """Display comprehensive quiz results"""
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0;'>Hasil Assessment Karir</h1>
        <p style='color: #f0f0f0; font-size: 1.1em; margin: 10px 0 0 0;'>Analisis Komprehensif Potensi Karir Anda</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.quiz_results:
        st.warning("Belum ada hasil quiz. Silakan kerjakan quiz terlebih dahulu!")
        if st.button("Kembali ke Home"):
            st.session_state.page = 'home'
            st.rerun()
        return
    
    # Display individual scores
    st.markdown("## Skor Individual")
    
    results = st.session_state.quiz_results
    col1, col2, col3, col4 = st.columns(4)
    
    # Ensure all scores are present, if not, default to 0 for display
    sjt_score = results.get('sjt', 0)
    personality_score = results.get('personality', 0)
    tech_score = results.get('tech', 0)
    soft_score = results.get('soft', 0)

    with col1:
        st.metric("SJT Score", f"{sjt_score:.1f}%", 
                 delta=f"{sjt_score-50:.1f}%" if sjt_score > 50 else f"{sjt_score-50:.1f}%")
    
    with col2:
        st.metric("Personality Score", f"{personality_score:.1f}%", 
                 delta=f"{personality_score-50:.1f}%" if personality_score > 50 else f"{personality_score-50:.1f}%")
    
    with col3:
        st.metric("Tech Score", f"{tech_score:.1f}%", 
                 delta=f"{tech_score-50:.1f}%" if tech_score > 50 else f"{tech_score-50:.1f}%")
    
    with col4:
        st.metric("Soft Skills Score", f"{soft_score:.1f}%", 
                 delta=f"{soft_score-50:.1f}%" if soft_score > 50 else f"{soft_score-50:.1f}%")
    
    # Radar chart for visualization
    st.markdown("## Profil Kompetensi")
    
    categories = ['SJT', 'Personality', 'Technical', 'Soft Skills']
    values = [sjt_score, personality_score, tech_score, soft_score]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Your Profile',
        line=dict(color='#667eea')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Profil Kompetensi Anda",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Career prediction
    st.markdown("## Prediksi Karir")
    
    # Check if all quizzes are completed before attempting prediction
    if 'sjt' in results and 'personality' in results and 'tech' in results and 'soft' in results:
        predicted_career = predict_career(sjt_score, personality_score, tech_score, soft_score)
        
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; background: #e9f5ff; border-radius: 10px; margin: 20px 0;'>
            <h3 style='color: #495057; margin: 0;'>Karir yang Cocok untuk Anda:</h3>
            <h2 style='color: #007bff; margin: 10px 0;'>{predicted_career}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Career recommendations
        st.markdown("## Rekomendasi Pengembangan")
        
        recommendations = get_career_recommendations(predicted_career, results)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Kekuatan Anda")
            for strength in recommendations['strengths']:
                st.markdown(f"- {strength}")
            
            st.markdown("### Area Pengembangan")
            for area in recommendations['areas_to_improve']:
                st.markdown(f"- {area}")
        
        with col2:
            st.markdown("### Langkah Selanjutnya")
            for action in recommendations['suggested_actions']:
                st.markdown(f"- {action}")
        
        # Overall assessment
        overall_score = (sjt_score + personality_score + tech_score + soft_score) / 4
        
        st.markdown("## Penilaian Keseluruhan")
        
        if overall_score >= 80:
            assessment = "Excellent - Anda memiliki profil yang sangat kuat!"
            color = "#28a745"
        elif overall_score >= 70:
            assessment = "Good - Profil yang baik dengan beberapa area untuk pengembangan"
            color = "#007bff"
        elif overall_score >= 60:
            assessment = "Average - Ada potensi bagus yang perlu dikembangkan"
            color = "#ffc107"
        else:
            assessment = "Needs Improvement - Fokus pada pengembangan skill fundamental"
            color = "#dc3545"
        
        st.markdown(f"""
        <div style='text-align: center; padding: 15px; background: {color}; color: white; border-radius: 8px; margin: 20px 0;'>
            <h4 style='margin: 0;'>Skor Keseluruhan: {overall_score:.1f}%</h4>
            <p style='margin: 5px 0 0 0;'>{assessment}</p>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.info("Silakan selesaikan semua quiz (SJT, Personality, Technical, Soft Skills) untuk melihat prediksi karir Anda.")
    
    if st.button("Simpan Hasil"):
        st.success("Hasil telah disimpan!")
        
    if st.button("Kembali ke Home"):
        st.session_state.page = 'home'
        st.rerun()
    
    st.markdown("## Evaluasi Model KNN")
    if st.button("Lihat Evaluasi Model"):
        show_model_evaluation()

def home_page():
    """Enhanced home page with better UI"""
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0; font-size: 2.5em;'>Career Assessment Platform</h1>
        <p style='color: #f0f0f0; font-size: 1.2em; margin: 10px 0 0 0;'>Temukan Potensi Karir Terbaikmu</p>
    </div>
    """, unsafe_allow_html=True)
    
    # User name input
    st.markdown("### Informasi Peserta")
    user_name = st.text_input("Masukkan nama Anda:", value=st.session_state.user_name)
    if user_name:
        st.session_state.user_name = user_name
    
    # Program description
    st.markdown("""
    ## Tentang Program Ini
    
    **Career Assessment Platform** adalah sistem penilaian karir komprehensif yang dirancang untuk membantu Anda mengidentifikasi potensi karir terbaik berdasarkan analisis multi-dimensi.
    
    ### Jenis Penilaian yang Tersedia:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Situational Judgment Test (SJT)**
        - Simulasi kasus nyata di tempat kerja
        - Menilai kemampuan pengambilan keputusan
        - Evaluasi respons terhadap situasi profesional
        """)
        
        st.markdown("""
        **Technical Skill Quiz**
        - Tes pengetahuan teknologi terkini
        - Mencakup programming, database, dan tools
        - Cocok untuk peran IT dan teknologi
        """)
    
    with col2:
        st.markdown("""
        **Personality Test**
        - Penilaian karakteristik kepribadian
        - Mengidentifikasi preferensi kerja
        - Evaluasi gaya komunikasi dan leadership
        """)
        
        st.markdown("""
        **Soft Skills Assessment**
        - Evaluasi kemampuan interpersonal
        - Penilaian adaptabilitas dan komunikasi
        - Mengukur emotional intelligence
        """)
    
    # Quiz completion status
    if st.session_state.quiz_results:
        st.markdown("### Status Quiz")
        st.markdown("**Quiz yang sudah diselesaikan:**")
        for quiz_type, score in st.session_state.quiz_results.items():
            st.markdown(f"- {quiz_type.upper()}: {score:.1f}%")
        
        if len(st.session_state.quiz_results) == 4: # Check if all 4 quizzes are completed
            st.success("Semua quiz selesai! Anda siap melihat hasil prediksi karir Anda.")
            if st.button("Lihat Hasil Lengkap", use_container_width=True):
                st.session_state.page = 'results'
                st.rerun()
        else:
            st.info(f"Anda telah menyelesaikan {len(st.session_state.quiz_results)}/4 quiz.")
            if st.button("Lihat Hasil Sementara", use_container_width=True):
                st.session_state.page = 'results'
                st.rerun()

    st.markdown("---")
    st.markdown("### Pilih Quiz yang Ingin Dikerjakan:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Mulai SJT", use_container_width=True):
            st.session_state.page = 'sjt'
            st.rerun()
        
        if st.button("Mulai Tech Quiz", use_container_width=True):
            st.session_state.page = 'tech'
            st.rerun()
    
    with col2:
        if st.button("Mulai Personality Test", use_container_width=True):
            st.session_state.page = 'personality'
            st.rerun()
        
        if st.button("Mulai Soft Skills", use_container_width=True):
            st.session_state.page = 'soft'
            st.rerun()

# Quiz data
sjt_questions = [
    {"q": "Atasan meminta kamu lembur padahal kamu memiliki rencana pribadi, apa yang kamu lakukan?", "options": ["Diskusi dan negosiasi", "Menolak", "Langsung lembur"]},
    {"q": "Rekan kerja sering terlambat mengirim data yang kamu butuhkan, tindakanmu?", "options": ["Mengingatkan baik-baik", "Membiarkan saja", "Melapor atasan"]},
    {"q": "Kamu melihat kesalahan prosedur yang dilakukan tim, tindakanmu?", "options": ["Memberi masukan", "Diam saja", "Mengikuti kesalahan"]},
    {"q": "Saat meeting, ide kamu ditolak tim, apa sikapmu?", "options": ["Menerima dan diskusi", "Kesal", "Diam saja"]},
    {"q": "Kamu mendapat tugas di luar jobdesc, apa yang kamu lakukan?", "options": ["Mengerjakan sambil diskusi", "Menolak", "Meninggalkan"]},
    {"q": "Klien meminta revisi mendadak, apa yang kamu lakukan?", "options": ["Prioritaskan revisi", "Menunda", "Menolak"]},
    {"q": "Rekan kerja meminta bantuan saat kamu sibuk, apa tindakanmu?", "options": ["Bantu jika bisa", "Menolak", "Menghindar"]},
    {"q": "Atasan marah padamu karena kesalahan tim, tindakanmu?", "options": ["Menjelaskan", "Diam", "Menyalahkan tim"]},
    {"q": "Kamu melihat rekan kerja melanggar aturan kantor, apa tindakanmu?", "options": ["Menegur baik-baik", "Membiarkan", "Melaporkan"]},
    {"q": "Kamu ditugaskan project baru mendadak, apa yang kamu lakukan?", "options": ["Mengatur prioritas", "Menolak", "Mengeluh"]},
]

personality_questions = [
    {"q": "Saya merasa senang bekerja dengan banyak orang.", "correct": 0}, 
    {"q": "Saya suka membuat rencana kerja sebelum memulai tugas.", "correct": 0}, 
    {"q": "Saya lebih suka pekerjaan yang stabil daripada yang penuh risiko.", "correct": 1}, 
    {"q": "Saya senang belajar hal baru untuk pengembangan diri.", "correct": 0}, 
    {"q": "Saya merasa nyaman ketika berbicara di depan banyak orang.", "correct": 0}, 
    {"q": "Saya senang memimpin kelompok atau tim.", "correct": 0}, 
    {"q": "Saya biasanya menyelesaikan pekerjaan tepat waktu.", "correct": 0}, 
    {"q": "Saya merasa nyaman bekerja dalam kondisi tekanan.", "correct": 0}, 
    {"q": "Saya suka menyelesaikan masalah yang kompleks.", "correct": 0}, 
    {"q": "Saya suka bekerja dengan detail dan ketelitian tinggi.", "correct": 0}, 
]

tech_questions = [
    {"q": "Apa itu Python?", "options": ["Bahasa Pemrograman", "Framework", "Database"], "correct": 0},
    {"q": "Manakah yang termasuk database?", "options": ["MySQL", "Photoshop", "Premiere"], "correct": 0},
    {"q": "Apa itu Git?", "options": ["Version Control", "Editor", "Bahasa Pemrograman"], "correct": 0},
    {"q": "HTML digunakan untuk?", "options": ["Membuat tampilan web", "Database", "Analisis data"], "correct": 0},
    {"q": "CSS digunakan untuk?", "options": ["Mengatur tampilan web", "Server", "Keamanan"], "correct": 0},
    {"q": "JavaScript digunakan untuk?", "options": ["Interaktif website", "Mengatur server", "Membuat database"], "correct": 0},
    {"q": "Framework untuk Machine Learning?", "options": ["TensorFlow", "Laravel", "Vue"], "correct": 0},
    {"q": "Apa itu API?", "options": ["Interface komunikasi aplikasi", "Bahasa pemrograman", "Framework"], "correct": 0},
    {"q": "Contoh NoSQL Database?", "options": ["MongoDB", "MySQL", "Oracle"], "correct": 0},
    {"q": "IDE adalah?", "options": ["Lingkungan pengembangan", "Bahasa pemrograman", "Framework"], "correct": 0},
    {"q": "Bahasa pemrograman untuk Data Science?", "options": ["Python", "HTML", "CSS"], "correct": 0},
    {"q": "Untuk desain antarmuka biasa digunakan?", "options": ["Figma", "SQL", "TensorFlow"], "correct": 0},
    {"q": "Untuk analisis data besar digunakan?", "options": ["Python", "Photoshop", "CorelDraw"], "correct": 0},
    {"q": "Framework backend populer?", "options": ["Django", "Vue", "React"], "correct": 0},
    {"q": "Manakah yang bukan bahasa pemrograman?", "options": ["Photoshop", "Python", "Java"], "correct": 0},
    {"q": "Untuk pengolahan data digunakan?", "options": ["Pandas", "HTML", "CSS"], "correct": 0},
    {"q": "Firebase digunakan untuk?", "options": ["Backend dan database", "Editor gambar", "Framework CSS"], "correct": 0},
    {"q": "Untuk testing code digunakan?", "options": ["PyTest", "Premiere", "Figma"], "correct": 0},
    {"q": "Bahasa untuk pengembangan Android?", "options": ["Kotlin", "HTML", "CSS"], "correct": 0},
    {"q": "Untuk membuat REST API digunakan?", "options": ["Flask/Django", "HTML", "CSS"], "correct": 0},
]

soft_questions = [
    {"q": "Bagaimana kamu menangani kritik?", "options": ["Menerima", "Menolak", "Menghindar"]},
    {"q": "Bagaimana kamu menyelesaikan konflik tim?", "options": ["Diskusi solusi", "Menghindar", "Diam saja"]},
    {"q": "Apa sikapmu terhadap deadline?", "options": ["Tepat waktu", "Menunda", "Menghindar"]},
    {"q": "Bagaimana kamu beradaptasi dengan perubahan?", "options": ["Fleksibel", "Menolak", "Sulit beradaptasi"]},
    {"q": "Bagaimana kamu mengatur waktu?", "options": ["Prioritas", "Menunda", "Acak"]},
    {"q": "Bagaimana kamu mengatasi tekanan kerja?", "options": ["Tetap tenang", "Panik", "Mengeluh"]},
    {"q": "Bagaimana kamu bekerja dalam tim?", "options": ["Kolaboratif", "Individu", "Menolak"]},
    {"q": "Bagaimana kamu meningkatkan diri?", "options": ["Belajar hal baru", "Diam saja", "Menunda"]},
    {"q": "Bagaimana kamu mengambil keputusan sulit?", "options": ["Analisis terlebih dahulu", "Asal memutuskan", "Menunda"]},
    {"q": "Bagaimana kamu menghadapi kritik negatif?", "options": ["Evaluasi dan perbaikan", "Kesal", "Menolak"]},
    {"q": "Bagaimana cara kamu memberi masukan pada teman kerja?", "options": ["Sopan dan jelas", "Menyindir", "Diam"]},
    {"q": "Bagaimana kamu berkomunikasi dalam tim?", "options": ["Terbuka dan efektif", "Tertutup", "Pasif"]},
    {"q": "Bagaimana kamu menyelesaikan masalah kompleks?", "options": ["Analisis dan diskusi", "Menghindar", "Menunda"]},
    {"q": "Bagaimana kamu memimpin tim?", "options": ["Memberi contoh baik", "Memaksa", "Diam"]},
    {"q": "Bagaimana kamu belajar hal baru?", "options": ["Inisiatif", "Menunda", "Menghindar"]},
    {"q": "Bagaimana kamu menjaga hubungan dengan rekan kerja?", "options": ["Komunikasi baik", "Menjauh", "Pasif"]},
    {"q": "Bagaimana kamu menangani tugas mendadak?", "options": ["Prioritaskan", "Mengeluh", "Menunda"]},
    {"q": "Bagaimana kamu mengevaluasi diri?", "options": ["Refleksi rutin", "Mengabaikan", "Menunda"]},
    {"q": "Bagaimana kamu memberi kritik membangun?", "options": ["Sopan dan jelas", "Menyindir", "Diam"]},
    {"q": "Bagaimana kamu menghadapi ketidakpastian?", "options": ["Fleksibel dan siap", "Menolak", "Mengeluh"]},
]

# Main application logic
if st.session_state.page == 'home':
    home_page()

elif st.session_state.page == 'results':
    display_results()

elif st.session_state.page == 'sjt':
    st.markdown("""
    <div style='text-align: center; padding: 15px; background: #e9f5ff; border-radius: 8px; margin-bottom: 20px;'>
        <h2 style='color: #495057; margin: 0;'>Situational Judgment Test (SJT)</h2>
        <p style='color: #6c757d; margin: 5px 0 0 0;'>Simulasi situasi nyata di tempat kerja</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'sjt_selected_questions' not in st.session_state:
        st.session_state.sjt_selected_questions = random.sample(sjt_questions, 5)
    
    answers = []
    for idx, q in enumerate(st.session_state.sjt_selected_questions):
        st.markdown(f"**{idx+1}. {q['q']}**")
        answer = st.radio("Pilih jawaban:", q['options'], key=f"sjt_{idx}", index=None)
        if answer is not None:
            answers.append(q['options'].index(answer))
        st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Kembali ke Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    
    with col2:
        if st.button("Selesai & Simpan Hasil", use_container_width=True):
            if len(answers) == len(st.session_state.sjt_selected_questions):
                score = calculate_score(answers, st.session_state.sjt_selected_questions, scoring_type='weighted')
                st.session_state.quiz_results['sjt'] = score
                st.success(f"SJT selesai! Skor Anda: {score:.1f}%")
                del st.session_state.sjt_selected_questions 
                st.session_state.page = 'results'
                st.rerun()
            else:
                st.error("Harap jawab semua pertanyaan!")

elif st.session_state.page == 'personality':
    st.markdown("""
    <div style='text-align: center; padding: 15px; background: #e9f5ff; border-radius: 8px; margin-bottom: 20px;'>
        <h2 style='color: #495057; margin: 0;'>Personality Test</h2>
        <p style='color: #6c757d; margin: 5px 0 0 0;'>Penilaian karakteristik kepribadian</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'personality_selected_questions' not in st.session_state:
        st.session_state.personality_selected_questions = random.sample(personality_questions, 5)
    
    answers = []
    for idx, q in enumerate(st.session_state.personality_selected_questions):
        st.markdown(f"**{idx+1}. {q['q']}**")
        answer_options = ["Setuju", "Tidak Setuju"]
        answer = st.radio("Pilih jawaban:", answer_options, key=f"pers_{idx}", index=None)
        if answer is not None:
            answers.append(answer_options.index(answer))
        st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Kembali ke Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    with col2:
        if st.button("Selesai & Simpan Hasil", use_container_width=True):
            if len(answers) == len(st.session_state.personality_selected_questions):
                score = calculate_score(answers, st.session_state.personality_selected_questions, scoring_type='percentage_correct')
                st.session_state.quiz_results['personality'] = score
                st.success(f"Personality Test selesai! Skor Anda: {score:.1f}%")
                del st.session_state.personality_selected_questions
                st.session_state.page = 'results'
                st.rerun()
            else:
                st.error("Harap jawab semua pertanyaan!")

elif st.session_state.page == 'tech':
    st.markdown("""
    <div style='text-align: center; padding: 15px; background: #e9f5ff; border-radius: 8px; margin-bottom: 20px;'>
        <h2 style='color: #495057; margin: 0;'>Technical Skill Quiz</h2>
        <p style='color: #6c757d; margin: 5px 0 0 0;'>Tes pengetahuan teknologi dan programming</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'tech_selected_questions' not in st.session_state:
        st.session_state.tech_selected_questions = []
        selected_raw_questions = random.sample(tech_questions, 10)
        
        for q_raw in selected_raw_questions:
            # Create a mutable copy of the question to avoid modifying the original list
            q_copy = q_raw.copy()
            
            # Get the correct answer text before shuffling
            correct_answer_text = q_copy['options'][q_copy['correct']]
            
            # Shuffle the options list in place
            random.shuffle(q_copy['options'])
            
            # Find the new index of the correct answer in the shuffled list
            q_copy['correct'] = q_copy['options'].index(correct_answer_text)
            
            st.session_state.tech_selected_questions.append(q_copy)
    
    answers = []
    for idx, q in enumerate(st.session_state.tech_selected_questions):
        st.markdown(f"**{idx+1}. {q['q']}**")
        answer = st.radio("Pilih jawaban:", q['options'], key=f"tech_{idx}", index=None)
        if answer is not None:
            answers.append(q['options'].index(answer))
        st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Kembali ke Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    
    with col2:
        if st.button("Selesai & Simpan Hasil", use_container_width=True):
            if len(answers) == len(st.session_state.tech_selected_questions):
                score = calculate_score(answers, st.session_state.tech_selected_questions, scoring_type='percentage_correct')
                st.session_state.quiz_results['tech'] = score
                st.success(f"Tech Quiz selesai! Skor Anda: {score:.1f}%")
                del st.session_state.tech_selected_questions
                st.session_state.page = 'results'
                st.rerun()
            else:
                st.error("Harap jawab semua pertanyaan!")

elif st.session_state.page == 'soft':
    st.markdown("""
    <div style='text-align: center; padding: 15px; background: #e9f5ff; border-radius: 8px; margin-bottom: 20px;'>
        <h2 style='color: #495057; margin: 0;'>Soft Skills Assessment</h2>
        <p style='color: #6c757d; margin: 5px 0 0 0;'>Evaluasi kemampuan interpersonal dan adaptabilitas</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'soft_selected_questions' not in st.session_state:
        st.session_state.soft_selected_questions = random.sample(soft_questions, 10)
    
    answers = []
    for idx, q in enumerate(st.session_state.soft_selected_questions):
        st.markdown(f"**{idx+1}. {q['q']}**")
        answer = st.radio("Pilih jawaban:", q['options'], key=f"soft_{idx}", index=None)
        if answer is not None:
            answers.append(q['options'].index(answer))
        st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Kembali ke Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    
    with col2:
        if st.button("Selesai & Simpan Hasil", use_container_width=True):
            if len(answers) == len(st.session_state.soft_selected_questions):
                score = calculate_score(answers, st.session_state.soft_selected_questions, scoring_type='weighted')
                st.session_state.quiz_results['soft'] = score
                st.success(f"Soft Skills Assessment selesai! Skor Anda: {score:.1f}%")
                del st.session_state.soft_selected_questions
                st.session_state.page = 'results'
                st.rerun()
            else:
                st.error("Harap jawab semua pertanyaan!")