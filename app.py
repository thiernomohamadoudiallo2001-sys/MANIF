import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Manifeste IA - Capture & Rapports",
    page_icon="🚢",
    layout="wide"
)

st.title("🚢 Manifeste IA - Numérisation & Gestion Maritime")
st.markdown("Prenez en photo vos documents de transport pour enregistrer automatiquement vos données et générer vos rapports mensuels.")

# Initialisation de l'état de session (base de données temporaire)
if "manifeste_df" not in st.session_state:
    # Structure identique aux fichiers MANIFESTE 2026
    st.session_state.manifeste_df = pd.DataFrame(columns=[
        "MONTHS", "Ligne", "VESSEL", "LOADING PORT", "consignee", 
        "COMMODITIES", "20'DV", "40'HC", "TEU's", "Trade", "Commodity-category"
    ])

# Navigation par onglets
tab1, tab2, tab3 = st.tabs(["📷 Numériser un document", "📊 Rapports Mensuels", "📁 Base de Données / Export"])

# --- ONGLET 1 : NUMÉRISATION PAR PHOTO ---
with tab1:
    st.header("1. Capture de document (Avis d'arrivée / B/L / Manifeste)")
    
    col_cam, col_form = st.columns([1, 1])
    
    with col_cam:
        st.subheader("Prise de vue")
        camera_photo = st.camera_input("Prendre une photo du document")
        uploaded_file = st.file_uploader("Ou importer une image / scan", type=["png", "jpg", "jpeg"])
        
        target_file = camera_photo if camera_photo is not None else uploaded_file

    with col_form:
        st.subheader("Informations Extraintes (Validation IA)")
        
        # Données d'exemple simulées par l'extraction OCR / IA
        extracted_data = {
            "MONTHS": datetime.now().strftime("%Y-%m-01"),
            "Ligne": "MAERSK",
            "VESSEL": "HAIAN GAMA - 550S",
            "LOADING PORT": "Jebel Ali",
            "consignee": "Ets Mamadou Diallo",
            "COMMODITIES": "General Marchandises",
            "20_DV": 0,
            "40_HC": 2,
            "Trade": "20-MIDDLE EAST",
            "Commodity-category": "General Housegoods"
        }

        if target_file:
            st.success("✅ Image analysée avec succès !")
        else:
            st.info("ℹ️ Prenez une photo ou chargez un fichier pour lancer l'extraction automatique. Vous pouvez également tester le formulaire ci-dessous.")

        # Formulaire de contrôle et de validation
        with st.form("validation_form"):
            months = st.text_input("Mois (AAAA-MM-JJ)", value=extracted_data["MONTHS"])
            ligne = st.selectbox("Ligne Maritime", ["MAERSK", "CMA CGM", "MSC", "COSCO", "ONE", "AUTRE"], index=0)
            vessel = st.text_input("Navire (VESSEL)", value=extracted_data["VESSEL"])
            loading_port = st.text_input("Port de Chargement (LOADING PORT)", value=extracted_data["LOADING PORT"])
            consignee = st.text_input("Consignataire (Consignee)", value=extracted_data["consignee"])
            commodities = st.text_input("Marchandises (COMMODITIES)", value=extracted_data["COMMODITIES"])
            
            c1, c2 = st.columns(2)
            with c1:
                c_20 = st.number_input("Nombre Conteneurs 20'DV", min_value=0, value=extracted_data["20_DV"], step=1)
            with c2:
                c_40 = st.number_input("Nombre Conteneurs 40'HC", min_value=0, value=extracted_data["40_HC"], step=1)
                
            # Calcul automatique des TEU (1 x 20'DV = 1 TEU, 1 x 40'HC = 2 TEUs)
            calculated_teus = (c_20 * 1) + (c_40 * 2)
            st.info(f"**TEU's Calculés :** {calculated_teus}")
            
            trade = st.text_input("Trade", value=extracted_data["Trade"])
            category = st.text_input("Catégorie de Marchandise", value=extracted_data["Commodity-category"])
            
            btn_submit = st.form_submit_button("💾 Enregistrer dans le Manifeste")
            
            if btn_submit:
                new_entry = {
                    "MONTHS": months,
                    "Ligne": ligne,
                    "VESSEL": vessel,
                    "LOADING PORT": loading_port,
                    "consignee": consignee,
                    "COMMODITIES": commodities,
                    "20'DV": c_20 if c_20 > 0 else None,
                    "40'HC": c_40 if c_40 > 0 else None,
                    "TEU's": calculated_teus,
                    "Trade": trade,
                    "Commodity-category": category
                }
                
                st.session_state.manifeste_df = pd.concat(
                    [st.session_state.manifeste_df, pd.DataFrame([new_entry])], 
                    ignore_index=True
                )
                st.balloons()
                st.success("L'enregistrement a été ajouté avec succès au manifeste !")

# --- ONGLET 2 : RAPPORTS MENSUELS ---
with tab2:
    st.header("📊 Rapports Mensuels & Statistiques")
    
    df = st.session_state.manifeste_df
    
    if df.empty:
        st.warning("Aucune donnée disponible. Veuillez enregistrer des conteneurs via l'onglet 'Numériser un document' ou charger un fichier Excel.")
    else:
        # Métriques clés
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total TEU's", int(df["TEU's"].sum()))
        col2.metric("Total 20'DV", int(df["20'DV"].fillna(0).sum()))
        col3.metric("Total 40'HC", int(df["40'HC"].fillna(0).sum()))
        col4.metric("Nombre d'expéditions", len(df))
        
        st.markdown("---")
        
        # Graphiques
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("Volume TEUs par Ligne Maritime")
            trade_chart = df.groupby("Ligne")["TEU's"].sum()
            st.bar_chart(trade_chart)
            
        with g2:
            st.subheader("Répartition des TEUs par Trade")
            trade_summary = df.groupby("Trade")["TEU's"].sum()
            st.pie_chart(trade_summary)
            
        st.subheader("Top Consignataires (Consignees)")
        top_consignees = df.groupby("consignee")["TEU's"].sum().reset_index().sort_values(by="TEU's", ascending=False)
        st.dataframe(top_consignees, use_container_width=True)

# --- ONGLET 3 : EXPORT & FICHIER EXCEL ---
with tab3:
    st.header("📁 Base de Données du Manifeste")
    
    st.dataframe(st.session_state.manifeste_df, use_container_width=True)
    
    # Bouton d'exportation au format Excel
    if not st.session_state.manifeste_df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.manifeste_df.to_excel(writer, sheet_name='Manifest', index=False)
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Télécharger le Manifeste en Excel (.xlsx)",
            data=processed_data,
            file_name=f"MANIFESTE_EXPORT_{datetime.now().strftime('%Y_%m_%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )