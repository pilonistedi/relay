<?php
// 1. DATABASE CONFIGURATION KEYS (Kept clean for your future Vercel migration)
$db_host = 'localhost';
$db_name = 'relay_workspace'; // Change this if you named your DB something else
$db_user = 'root';
$db_pass = '';

try {
    // Establish a secure PDO collection link
    $pdo = new PDO("mysql:host=$db_host;dbname=$db_name;charset=utf8mb4", $db_user, $db_pass, [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
    ]);
} catch (PDOException $e) {
    die("Database Connection failed: " . $e->getMessage());
}

// 2. TAILWIND THEME TRANSLATION MAP (Maps string column colors to exact Tailwind classes)
$themeMap = [
    'blue' => [
        'hover_border' => 'hover:border-blue-500/40',
        'glow_shadow'  => 'hover:shadow-[0_0_25px_rgba(59,130,246,0.12)]',
        'badge_text'   => 'text-blue-400',
        'badge_bg'     => 'bg-blue-500/20 border-blue-500/20',
        'btn_bg'       => 'bg-blue-500 hover:bg-blue-400 text-neutral-950'
    ],
    'cyan' => [
        'hover_border' => 'hover:border-cyan-500/40',
        'glow_shadow'  => 'hover:shadow-[0_0_25px_rgba(6,182,212,0.12)]',
        'badge_text'   => 'text-cyan-400',
        'badge_bg'     => 'bg-cyan-500/20 border-cyan-500/20',
        'btn_bg'       => 'bg-cyan-500 hover:bg-cyan-400 text-neutral-950'
    ],
    'purple' => [
        'hover_border' => 'hover:border-purple-500/40',
        'glow_shadow'  => 'hover:shadow-[0_0_25px_rgba(168,85,247,0.12)]',
        'badge_text'   => 'text-purple-400',
        'badge_bg'     => 'bg-purple-500/20 border-purple-500/20',
        'btn_bg'       => 'bg-purple-500 hover:bg-purple-400 text-neutral-950'
    ],
    'emerald' => [
        'hover_border' => 'hover:border-emerald-500/40',
        'glow_shadow'  => 'hover:shadow-[0_0_25px_rgba(16,185,129,0.12)]',
        'badge_text'   => 'text-emerald-400',
        'badge_bg'     => 'bg-emerald-500/20 border-emerald-500/20',
        'btn_bg'       => 'bg-emerald-500 hover:bg-emerald-400 text-neutral-950'
    ],
    'amber' => [
        'hover_border' => 'hover:border-amber-500/40',
        'glow_shadow'  => 'hover:shadow-[0_0_25px_rgba(245,158,11,0.12)]',
        'badge_text'   => 'text-amber-400',
        'badge_bg'     => 'bg-amber-500/20 border-amber-500/20',
        'btn_bg'       => 'bg-amber-500 hover:bg-amber-400 text-neutral-950'
    ],
    'rose' => [
        'hover_border' => 'hover:border-rose-500/40',
        'glow_shadow'  => 'hover:shadow-[0_0_25px_rgba(244,63,94,0.12)]',
        'badge_text'   => 'text-rose-400',
        'badge_bg'     => 'bg-rose-500/20 border-rose-500/20',
        'btn_bg'       => 'bg-rose-500 hover:bg-rose-400 text-neutral-950'
    ]
];

// 3. FETCH PIPELINE SLOTS FROM DATABASE
$stmt = $pdo->query("SELECT * FROM pipeline_slots ORDER BY slot_number ASC");
$slots = $stmt->fetchAll();
?>