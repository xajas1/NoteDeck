with open("/Users/tim/NoteDeck/MainDeck-modular/Sources/EFT1_Kraus25/EFT1_Kraus25.pdf", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, start=1):
        for ch in line:
            if ord(ch) < 32 and ch not in '\t\n\r':
                print(f"Zeile {i}: Problematisches Zeichen -> {repr(ch)} (Unicode: {ord(ch):04X})")
