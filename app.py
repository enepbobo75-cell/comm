from flask import Flask, render_template, request, redirect, url_for
from config import get_connection
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(quantite * prix_applique), 0) FROM contenir")
    ca_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ventes")
    nb_ventes = cur.fetchone()[0]
    cur.execute("""
        SELECT COALESCE(SUM(c.quantite * c.prix_applique), 0)
        FROM ventes v
        JOIN contenir c ON c.num_ventes = v.num_ventes
        WHERE DATE_TRUNC('month', v.date_vente) = DATE_TRUNC('month', CURRENT_DATE)
    """)
    ca_mois = cur.fetchone()[0]
    cur.execute("SELECT SUM(stock_dispo) FROM articles")
    stock_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM articles WHERE stock_dispo < 10")
    articles_critiques = cur.fetchone()[0]
    cur.execute("SELECT * FROM top_articles LIMIT 5")
    top_articles = cur.fetchall()
    cur.execute("SELECT * FROM ca_journalier LIMIT 7")
    ca_jours = cur.fetchall()
    cur.execute("""
        SELECT 
            DATE_TRUNC('month', v.date_vente)::date AS mois,
            SUM(c.quantite * c.prix_applique) AS chiffre_affaires,
            COUNT(DISTINCT v.num_ventes) AS nombre_ventes
        FROM ventes v
        JOIN contenir c ON c.num_ventes = v.num_ventes
        GROUP BY DATE_TRUNC('month', v.date_vente)::date
        ORDER BY mois DESC
        LIMIT 6
    """)
    ca_mois_liste = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', ca_total=ca_total, nb_ventes=nb_ventes,
                           ca_mois=ca_mois, stock_total=stock_total,
                           articles_critiques=articles_critiques,
                           top_articles=top_articles,
                           ca_jours=ca_jours, ca_mois_liste=ca_mois_liste)

@app.route('/ventes')
def ventes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM detail_ventes")
    ventes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('ventes.html', ventes=ventes)

@app.route('/articles')
def articles():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM articles ORDER BY num_art")
    articles = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('articles.html', articles=articles)

@app.route('/nouvelle_vente', methods=['GET', 'POST'])
def nouvelle_vente():
    conn = get_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nom_client    = request.form['nom_client']
        prenom_client = request.form.get('prenom_client', '')
        numero_client = request.form.get('numero_client', '')
        num_art  = request.form['num_art']
        quantite = int(request.form['quantite'])
        remise   = float(request.form.get('remise', 0))
        cur.execute("SELECT num_clt FROM clients WHERE nom = %s AND prenom = %s",
                    (nom_client, prenom_client))
        client = cur.fetchone()
        if client:
            num_clt = client[0]
        else:
            cur.execute("INSERT INTO clients (nom, prenom, numero) VALUES (%s, %s, %s) RETURNING num_clt",
                        (nom_client, prenom_client, numero_client))
            num_clt = cur.fetchone()[0]
        cur.execute("SELECT prix_de_base FROM articles WHERE num_art = %s", (num_art,))
        prix = cur.fetchone()[0]
        prix_apres_remise = prix * (1 - remise / 100)
        montant = prix_apres_remise * quantite
        cur.execute("INSERT INTO ventes (num_clt) VALUES (%s) RETURNING num_ventes", (num_clt,))
        num_ventes = cur.fetchone()[0]
        cur.execute("INSERT INTO contenir (num_ventes, num_art, quantite, prix_applique) VALUES (%s, %s, %s, %s)",
                    (num_ventes, num_art, quantite, prix_apres_remise))
        cur.execute("UPDATE articles SET stock_dispo = stock_dispo - %s WHERE num_art = %s",
                    (quantite, num_art))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('ventes'))
    cur.execute("SELECT * FROM articles WHERE stock_dispo > 0 ORDER BY nom")
    articles = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('nouvelle_vente.html', articles=articles)

@app.route('/nouvel_article', methods=['GET', 'POST'])
def nouvel_article():
    conn = get_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nom      = request.form['nom']
        pointure = request.form.get('pointure', '')
        couleur  = request.form.get('couleur', '')
        type_art = request.form.get('type', '')
        marque   = request.form.get('marque', '')
        prix     = float(request.form['prix_de_base'])
        stock    = int(request.form['stock_dispo'])
        cur.execute("""INSERT INTO articles (nom, pointure, couleur, type, marque, prix_de_base, stock_dispo)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (nom, pointure, couleur, type_art, marque, prix, stock))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('articles'))
    cur.close()
    conn.close()
    return render_template('nouvel_article.html')

if __name__ == '__main__':
    app.run(debug=True)