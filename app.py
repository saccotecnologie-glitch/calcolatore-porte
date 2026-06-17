def disegno_porta(ante, tipo, luce_mm, altezza_mm, lunghezza_traversa):
    colore_traversa = "#111111"
    colore_vetro = "#d9e3ea"
    colore_telaio = "#222222"
    colore_quote = "#111111"

    if ante == "1 anta":
        anta_mobile = int(luce_mm)
        anta_fissa = int(luce_mm)

        return f"""
        <svg width="100%" height="360" viewBox="0 0 760 360">
            <rect x="70" y="35" width="620" height="34" rx="3" fill="{colore_traversa}"/>
            <text x="380" y="27" text-anchor="middle" font-size="15" fill="{colore_quote}" font-weight="bold">
                TRAVERSA {int(lunghezza_traversa * 1000)} mm
            </text>

            <rect x="120" y="95" width="520" height="170" fill="#f7f7f7" stroke="{colore_telaio}" stroke-width="4"/>

            <rect x="140" y="115" width="235" height="130" fill="{colore_vetro}" stroke="{colore_telaio}" stroke-width="3"/>
            <rect x="385" y="115" width="235" height="130" fill="#eef3f6" stroke="{colore_telaio}" stroke-width="3"/>

            <line x1="380" y1="100" x2="380" y2="260" stroke="{colore_telaio}" stroke-width="4"/>

            <line x1="120" y1="295" x2="640" y2="295" stroke="{colore_quote}" stroke-width="2"/>
            <line x1="120" y1="285" x2="120" y2="305" stroke="{colore_quote}" stroke-width="2"/>
            <line x1="640" y1="285" x2="640" y2="305" stroke="{colore_quote}" stroke-width="2"/>
            <text x="380" y="320" text-anchor="middle" font-size="17" fill="{colore_quote}" font-weight="bold">
                LUCE PASSAGGIO {luce_mm} mm
            </text>

            <line x1="675" y1="95" x2="675" y2="265" stroke="{colore_quote}" stroke-width="2"/>
            <line x1="665" y1="95" x2="685" y2="95" stroke="{colore_quote}" stroke-width="2"/>
            <line x1="665" y1="265" x2="685" y2="265" stroke="{colore_quote}" stroke-width="2"/>
            <text x="710" y="185" text-anchor="middle" font-size="16" fill="{colore_quote}" font-weight="bold" transform="rotate(90 710,185)">
                H {altezza_mm} mm
            </text>

            <path d="M430 175 L560 175" stroke="#111111" stroke-width="5" marker-end="url(#arrow1)"/>
            <text x="380" y="350" text-anchor="middle" font-size="20" fill="#111111" font-weight="bold">
                PORTA AUTOMATICA 1 ANTA
            </text>

            <defs>
                <marker id="arrow1" markerWidth="12" markerHeight="12" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L7,3 z" fill="#111111"/>
                </marker>
            </defs>
        </svg>
        """

    else:
        return f"""
        <svg width="100%" height="360" viewBox="0 0 760 360">
            <rect x="70" y="35" width="620" height="34" rx="3" fill="{colore_traversa}"/>
            <text x="380" y="27" text-anchor="middle" font-size="15" fill="{colore_quote}" font-weight="bold">
                TRAVERSA {int(lunghezza_traversa * 1000)} mm
            </text>

            <rect x="120" y="95" width="520" height="170" fill="#f7f7f7" stroke="{colore_telaio}" stroke-width="4"/>

            <rect x="140" y="115" width="235" height="130" fill="{colore_vetro}" stroke="{colore_telaio}" stroke-width="3"/>
            <rect x="385" y="115" width="235" height="130" fill="{colore_vetro}" stroke="{colore_telaio}" stroke-width="3"/>

            <line x1="380" y1="100" x2="380" y2="260" stroke="{colore_telaio}" stroke-width="4"/>

            <path d="M340 175 L220 175" stroke="#111111" stroke-width="5" marker-end="url(#arrowL)"/>
            <path d="M420 175 L540 175" stroke="#111111" stroke-width="5" marker-end="url(#arrowR)"/>

            <line x1="120" y1="295" x2="640" y2="295" stroke="{colore_quote}" stroke-width="2"/>
            <line x1="120" y1="285" x2="120" y2="305" stroke="{colore_quote}" stroke-width="2"/>
            <line x1="640" y1="285" x2="640" y2="305" stroke="{colore_quote}" stroke-width="2"/>
            <text x="380" y="320" text-anchor="middle" font-size="17" fill="{colore_quote}" font-weight="bold">
                LUCE PASSAGGIO {luce_mm} mm
            </text>

            <line x1="675" y1="95" x2="675" y2="265" stroke="{colore_quote}" stroke-width="2"/>
            <line x1="665" y1="95" x2="685" y2="95" stroke="{colore_quote}" stroke-width="2"/>
            <line x1="665" y1="265" x2="685" y2="265" stroke="{colore_quote}" stroke-width="2"/>
            <text x="710" y="185" text-anchor="middle" font-size="16" fill="{colore_quote}" font-weight="bold" transform="rotate(90 710,185)">
                H {altezza_mm} mm
            </text>

            <text x="380" y="350" text-anchor="middle" font-size="20" fill="#111111" font-weight="bold">
                PORTA AUTOMATICA 2 ANTE
            </text>

            <defs>
                <marker id="arrowR" markerWidth="12" markerHeight="12" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L7,3 z" fill="#111111"/>
                </marker>
                <marker id="arrowL" markerWidth="12" markerHeight="12" refX="1" refY="3" orient="auto">
                    <path d="M7,0 L7,6 L0,3 z" fill="#111111"/>
                </marker>
            </defs>
        </svg>
        """
