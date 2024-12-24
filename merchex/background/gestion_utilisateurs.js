const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const router = express.Router();

// config/database.js
const { Sequelize } = require('sequelize');

// Se connecte à la base de données Django EXISTANTE
const sequelize = new Sequelize({
  dialect: 'postgres',  // ou 'mysql' selon ce que vous utilisez dans Django
  host: 'localhost',    // même host que dans settings.py
  database: 'nom_de_votre_base_django',  // le nom dans settings.py
  username: 'votre_utilisateur_django',  // l'utilisateur dans settings.py
  password: 'votre_mot_de_passe_django', // le mot de passe dans settings.py
  define: {
    timestamps: false,  // important pour la compatibilité avec Django
  }
});

module.exports = sequelize;

// Middleware d'authentification
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ message: 'Token manquant' });
    }

    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({ message: 'Token invalide' });
        }
        req.user = user;
        next();
    });
};

// Inscription
router.post('/register', async (req, res) => {
    try {
        const { email, password, username } = req.body;

        // Vérification si l'utilisateur existe déjà
        if (users.find(u => u.email === email)) {
            return res.status(400).json({ message: 'Cet email est déjà utilisé' });
        }

        // Hashage du mot de passe
        const hashedPassword = await bcrypt.hash(password, 10);

        // Création du nouvel utilisateur
        const newUser = {
            id: Date.now().toString(),
            email,
            username,
            password: hashedPassword,
            createdAt: new Date(),
            role: 'user'
        };

        users.push(newUser);

        res.status(201).json({
            message: 'Utilisateur créé avec succès',
            user: { id: newUser.id, email: newUser.email, username: newUser.username }
        });
    } catch (error) {
        res.status(500).json({ message: 'Erreur lors de l inscription', error: error.message });
    }
});

// Connexion
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        const user = users.find(u => u.email === email);

        if (!user) {
            return res.status(401).json({ message: 'Email ou mot de passe incorrect' });
        }

        const validPassword = await bcrypt.compare(password, user.password);
        if (!validPassword) {
            return res.status(401).json({ message: 'Email ou mot de passe incorrect' });
        }

        const token = jwt.sign(
            { id: user.id, email: user.email, role: user.role },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.json({
            message: 'Connexion réussie',
            token,
            user: { id: user.id, email: user.email, username: user.username }
        });
    } catch (error) {
        res.status(500).json({ message: 'Erreur lors de la connexion', error: error.message });
    }
});

// Obtenir le profil utilisateur
router.get('/profil', authenticateToken, (req, res) => {
    const user = users.find(u => u.id === req.user.id);
    if (!user) {
        return res.status(404).json({ message: 'Utilisateur non trouvé' });
    }
    
    const { password, ...userWithoutPassword } = user;
    res.json(userWithoutPassword);
});

// Modifier le profil utilisateur
router.put('/profil', authenticateToken, async (req, res) => {
    try {
        const { username, currentPassword, newPassword } = req.body;
        const userIndex = users.findIndex(u => u.id === req.user.id);

        if (userIndex === -1) {
            return res.status(404).json({ message: 'Utilisateur non trouvé' });
        }

        const updates = {};
        
        if (username) {
            updates.username = username;
        }

        if (currentPassword && newPassword) {
            const validPassword = await bcrypt.compare(currentPassword, users[userIndex].password);
            if (!validPassword) {
                return res.status(401).json({ message: 'Mot de passe actuel incorrect' });
            }
            updates.password = await bcrypt.hash(newPassword, 10);
        }

        users[userIndex] = { ...users[userIndex], ...updates };
        
        const { password, ...userWithoutPassword } = users[userIndex];
        res.json({ message: 'Profil mis à jour avec succès', user: userWithoutPassword });
    } catch (error) {
        res.status(500).json({ message: 'Erreur lors de la mise à jour du profil', error: error.message });
    }
});

// Liste des utilisateurs (admin seulement)
router.get('/users', authenticateToken, (req, res) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ message: 'Accès non autorisé' });
    }

    const usersWithoutPasswords = users.map(({ password, ...user }) => user);
    res.json(usersWithoutPasswords);
});

module.exports = router;