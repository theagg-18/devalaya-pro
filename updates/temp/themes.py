"""
Theme Configuration for Devalaya Pro
Defines color palettes for different temple aesthetics
"""

THEMES = {
    'kerala': {
        'name': 'Kerala Temple',
        'description': 'Traditional Kumkum and Chandan colors',
        'colors': {
            'primary': '#8B0000',      # Deep Maroon (Kumkum)
            'secondary': '#DAA520',    # Goldenrod (Chandan)
            'background': '#FDF5E6',   # Creamy White
            'surface': '#FFFFFF',      # Pure White
            'text_main': '#2C2C2C',    # Dark Charcoal
            'text_muted': '#64748b',   # Slate Gray
            'success': '#2E7D32',      # Temple Green
        }
    },
    'modern_blue': {
        'name': 'Modern Blue',
        'description': 'Contemporary blue and amber theme',
        'colors': {
            'primary': '#3B82F6',      # Bright Blue
            'secondary': '#F59E0B',    # Amber
            'background': '#F8FAFC',   # Light Gray
            'surface': '#FFFFFF',      # Pure White
            'text_main': '#1E293B',    # Slate
            'text_muted': '#64748b',   # Slate Gray
            'success': '#10B981',      # Emerald
        }
    },
    'royal_purple': {
        'name': 'Royal Purple',
        'description': 'Majestic purple and gold theme',
        'colors': {
            'primary': '#7C3AED',      # Purple
            'secondary': '#F59E0B',    # Gold
            'background': '#FAF5FF',   # Light Purple
            'surface': '#FFFFFF',      # Pure White
            'text_main': '#1F2937',    # Dark Gray
            'text_muted': '#6B7280',   # Gray
            'success': '#059669',      # Green
        }
    },
    'traditional_saffron': {
        'name': 'Traditional Saffron',
        'description': 'Sacred saffron and deep blue theme',
        'colors': {
            'primary': '#FF6B35',      # Saffron Orange
            'secondary': '#004E89',    # Deep Blue
            'background': '#FFF8F0',   # Warm White
            'surface': '#FFFFFF',      # Pure White
            'text_main': '#2D3748',    # Charcoal
            'text_muted': '#718096',   # Gray
            'success': '#38A169',      # Green
        }
    },
    'forest_harmony': {
        'name': 'Forest Harmony',
        'description': 'Deep greens and soft creams',
        'colors': {
            'primary': '#1E4620',      # Dark Forest Green
            'secondary': '#8FBC8F',    # Dark Sea Green
            'background': '#F1F8E9',   # Light Greenish White
            'surface': '#FFFFFF',      # Pure White
            'text_main': '#1B2E1B',    # Dark Greenish Black
            'text_muted': '#556B2F',   # Olive Drab
            'success': '#4CAF50',      # Green
        }
    },
    'ocean_breeze': {
        'name': 'Ocean Breeze',
        'description': 'Teals and refreshing blues',
        'colors': {
            'primary': '#00695C',      # Teal
            'secondary': '#4DB6AC',    # Light Teal
            'background': '#E0F2F1',   # Very Light Teal
            'surface': '#FFFFFF',      # Pure White
            'text_main': '#004D40',    # Dark Teal
            'text_muted': '#00796B',   # Medium Teal
            'success': '#00897B',      # Teal Green
        }
    },
    'sunset_glow': {
        'name': 'Sunset Glow',
        'description': 'Warm oranges and reddish-browns',
        'colors': {
            'primary': '#BF360C',      # Deep Orange
            'secondary': '#FFAB91',    # Light Deep Orange
            'background': '#FBE9E7',   # Very Light Deep Orange
            'surface': '#FFFFFF',      # Pure White
            'text_main': '#3E2723',    # Dark Brown
            'text_muted': '#6D4C41',   # Brown
            'success': '#FF7043',      # Light Orange
        }
    }
}

def get_theme(theme_name='kerala'):
    """Get theme configuration by name"""
    return THEMES.get(theme_name, THEMES['kerala'])

def get_all_themes():
    """Get all available themes"""
    return THEMES

def adjust_color(hex_color, amount):
    """Adjust color brightness (amount < 0 for darker, > 0 for lighter)"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    r = max(0, min(255, int(r * (1 + amount))))
    g = max(0, min(255, int(g * (1 + amount))))
    b = max(0, min(255, int(b * (1 + amount))))
    
    return f"#{r:02x}{g:02x}{b:02x}"

def hex_to_rgb(hex_color):
    """Convert hex to rgb string 'r, g, b'"""
    hex_color = hex_color.lstrip('#')
    return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"

def get_theme_css(theme_name='kerala', custom_colors=None):
    """Generate CSS variables for a theme"""
    if theme_name == 'custom' and custom_colors:
        # Use custom configuration
        colors = {
            'primary': custom_colors.get('primary', '#000000'),
            'secondary': custom_colors.get('secondary', '#ffffff'),
            'background': custom_colors.get('background', '#f5f5f5'),
            'surface': '#FFFFFF',
            'text_main': '#2C2C2C',
            'text_muted': '#64748b',
            'success': '#4CAF50'
        }
    else:
        theme = get_theme(theme_name)
        colors = theme['colors']
    
    # Calculate derived colors
    primary_hover = adjust_color(colors['primary'], -0.15) # 15% darker
    primary_rgb = hex_to_rgb(colors['primary'])
    accent_rgb = hex_to_rgb(colors['secondary'])
    
    css = f"""
    :root {{
        --primary: {colors['primary']};
        --primary-hover: {primary_hover};
        --primary-rgb: {primary_rgb};
        
        --accent: {colors['secondary']};
        --accent-rgb: {accent_rgb};
        
        --bg: {colors['background']};
        --surface: {colors['surface']};
        --text-main: {colors['text_main']};
        --text-muted: {colors['text_muted']};
        --success: {colors['success']};
    }}
    """
    return css
