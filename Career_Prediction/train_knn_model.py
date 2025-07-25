import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# Buat folder models jika belum ada
os.makedirs("models", exist_ok=True)
# Buat folder visualizations jika belum ada
os.makedirs("visualizations", exist_ok=True)

# Load dataset dari folder data/
dataset_path = os.path.join("data", "combined_career_dataset.csv")
df = pd.read_csv(dataset_path)

# --- Tambahan untuk Pembersihan dan Validasi Data (Bukti Hasil untuk 3.3.2) ---
print("\n--- Informasi Dataset (df.info()) ---")
df.info() # Ini akan mencetak informasi ringkasan DataFrame ke konsol

print("\n--- Statistik Deskriptif Dataset (df.describe()) ---")
print(df.describe().to_string()) # .to_string() agar semua baris/kolom tampil lengkap di konsol
# --- Akhir Tambahan untuk Pembersihan dan Validasi Data ---


# Pisahkan fitur dan label
X = df[['tech_score', 'soft_score', 'sjt_score', 'personality_score']]
y = df['career']

# Encode label karier
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# --- Tambahan untuk Encoding Label Kategori Karier (Bukti Hasil untuk 3.3.3) ---
print("\n--- Encoding Label Kategori Karier ---")
print("Kelas Karir Asli:", le.classes_)
print("Contoh Mapping (5 label pertama):")
# Ambil beberapa contoh label asli dan hasil encodingnya
# Pastikan y.unique() ada isinya sebelum mengambil slice
if len(y.unique()) > 0:
    sample_labels = y.unique()[:min(5, len(y.unique()))] # Ambil hingga 5 label unik pertama, atau kurang jika tidak cukup
    for label in sample_labels:
        encoded_value = le.transform([label])[0]
        print(f"  '{label}' -> {encoded_value}")
else:
    print("Tidak ada label unik ditemukan di kolom 'career'.")


# Contoh inverse transform (ambil nilai encoded pertama jika ada)
if len(y_encoded) > 0:
    example_encoded_value = y_encoded[0]
    decoded_label = le.inverse_transform([example_encoded_value])[0]
    print(f"  Encoded '{example_encoded_value}' -> Decoded '{decoded_label}'")
else:
    print("Tidak ada data terenkode untuk contoh inverse transform.")
# --- Akhir Tambahan untuk Encoding Label ---


# Normalisasi data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X) # Lakukan scaling pada seluruh X untuk visualisasi

# --- Visualisasi Distribusi Fitur Sebelum Normalisasi ---
plt.figure(figsize=(15, 5))
features_list = ['tech_score', 'soft_score', 'sjt_score', 'personality_score']
for i, feature in enumerate(features_list):
    plt.subplot(1, 4, i + 1)
    sns.histplot(X[feature], kde=True)
    plt.title(f'Distribusi {feature} (Sebelum Scaling)')
    plt.xlabel('Nilai Skor')
    plt.ylabel('Frekuensi')
plt.tight_layout()
plt.savefig('visualizations/distribusi_sebelum_scaling.png')
plt.close()

# --- Visualisasi Distribusi Fitur Setelah Normalisasi ---
df_scaled_viz = pd.DataFrame(X_scaled, columns=features_list)
plt.figure(figsize=(15, 5))
for i, feature in enumerate(features_list):
    plt.subplot(1, 4, i + 1)
    sns.histplot(df_scaled_viz[feature], kde=True)
    plt.title(f'Distribusi {feature} (Setelah Scaling)')
    plt.xlabel('Nilai Skor (Skala)')
    plt.ylabel('Frekuensi')
    plt.xlim(-3, 3) # Batasi sumbu X untuk melihat efek scaling lebih jelas
plt.tight_layout()
plt.savefig('visualizations/distribusi_setelah_scaling.png')
plt.close()

print("Visualisasi distribusi sebelum dan setelah scaling telah disimpan di folder 'visualizations/'.")

# Split data (gunakan X_scaled yang sudah dinormalisasi)
X_train_scaled, X_test_scaled, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, stratify=y_encoded, random_state=42)

# --- Tambahan untuk Pemisahan Data (Bukti Hasil untuk 3.3.5) ---
print("\n--- Ukuran Data Training dan Testing Set ---")
print(f"X_train_scaled shape: {X_train_scaled.shape}")
print(f"X_test_scaled shape: {X_test_scaled.shape}")
print(f"y_train shape: {y_train.shape}")
print(f"y_test shape: {y_test.shape}")
# --- Akhir Tambahan untuk Pemisahan Data ---


# Latih model KNN
knn = KNeighborsClassifier(n_neighbors=5, weights='distance')
knn.fit(X_train_scaled, y_train)

# Evaluasi model
y_pred = knn.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred, target_names=le.classes_)
cm = confusion_matrix(y_test, y_pred)

# Simpan model dan encoder
joblib.dump(knn, "models/knn_model.joblib")
joblib.dump(le, "models/label_encoder.joblib")
joblib.dump(scaler, "models/scaler.joblib")

# Simpan evaluasi ke file teks
df_cm = pd.DataFrame(cm, index=le.classes_, columns=le.classes_)
output_lines = [
    f"Akurasi: {accuracy*100:.2f}%\n",
    "Classification Report:\n",
    report,
    "\nConfusion Matrix:\n",
    df_cm.to_string()
]
with open("models/model_evaluation_detailed.txt", "w") as f:
    f.write("\n".join(output_lines))

# Simpan confusion matrix sebagai gambar PNG
plt.figure(figsize=(8, 6))
sns.heatmap(df_cm, annot=True, fmt="d", cmap="Blues", cbar=True)
plt.title("Confusion Matrix")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig("models/confusion_matrix.png")
plt.close() # Penting: Tutup plot setelah disimpan

print("✅ Model, evaluasi, dan gambar confusion matrix berhasil disimpan ke folder 'models'.")