import { useLocation, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import styles from "./Sidebar.module.css";

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const menuItems = [
    {
        name: "Mission Control",
        href: "/",
        icon: (
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
            </svg>
        ),
    },
    {
        name: "Project Intercept",
        href: "/projects",
        icon: (
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
            </svg>
        ),
    },
    {
        name: "Tactical Proposals",
        href: "/templates",
        icon: (
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
        ),
    },
    {
        name: "Operative Profile",
        href: "/profile",
        icon: (
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="7" r="4" />
                <path d="M5.5 21a8.38 8.38 0 0 1 13 0" />
            </svg>
        ),
    },
    {
        name: "Mission History",
        href: "/history",
        icon: (
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 8v4l3 3" />
                <circle cx="12" cy="12" r="10" />
            </svg>
        ),
    },
    {
        name: "System Config",
        href: "/settings",
        icon: (
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
        ),
    },
];

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
    const location = useLocation();
    const pathname = location.pathname;
    const { user, signOut } = useAuth();

    return (
        <aside className={`sidebar ${isOpen ? 'open' : ''} ${styles.sidebar}`}>
            {/* Mobile Close Button */}
            <button className={`${styles.closeBtn} mobile-only btn btn-ghost`} onClick={onClose}>
                <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>

            {/* Logo */}
            <div className={styles.logo}>
                <div className={styles.logoIcon}>
                    <img 
                        src="https://media.licdn.com/dms/image/sync/v2/D4D27AQEiu3OUtuPafw/articleshare-shrink_800/B4DZmh2H6fJIAM-/0/1759356944429?e=2147483647&v=beta&t=RtaLDLIZf-4r34Z-ETQzA4mmzZRdYCEYXuV07qeXdDk" 
                        alt="Workana Logo" 
                        className={styles.officialLogo}
                    />
                    <div className={styles.statusPulse}></div>
                </div>
                <div className={styles.logoText}>
                    <h1>Workana</h1>
                    <div className={styles.subtextContainer}>
                        <span className={styles.subtextMain}>AUTOMATION</span>
                        <span className={styles.subtextStatus}>• SYSTEM ACTIVE</span>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className={styles.nav}>
                {menuItems.map((item) => (
                    <Link
                        key={item.href}
                        to={item.href}
                        className={`${styles.navItem} ${pathname === item.href ? styles.active : ""}`}
                        onClick={() => {
                            if (window.innerWidth <= 1024) onClose();
                        }}
                    >
                        {item.icon}
                        <span>{item.name}</span>
                    </Link>
                ))}
            </nav>

            {/* Footer */}
            <div className={styles.footer} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div className={styles.userInfo}>
                    <div className={styles.avatar} />

                    <div className={styles.userDetails}>
                        <span className={styles.userName} title={user?.email || "Operador"}>
                            {user?.email ? user.email.split("@")[0] : "Operador"}
                        </span>
                        <span className={styles.userStatus}>Plano Premium</span>
                    </div>
                </div>

                <button 
                    onClick={signOut}
                    style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        marginTop: '12px',
                        padding: '10px',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: '8px',
                        color: '#ef4444',
                        background: 'rgba(239, 68, 68, 0.05)',
                        cursor: 'pointer',
                        fontWeight: '600',
                        fontSize: '0.85rem',
                        transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)';
                        e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(239, 68, 68, 0.05)';
                        e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.2)';
                    }}
                >
                    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span>Terminar Sessão</span>
                </button>
            </div>
        </aside>
    );
}
