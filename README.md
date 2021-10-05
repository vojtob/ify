# ify - iconify images

Základné funkcie programu:
1. Konverzia obrázkov z svg, umlet, mermaid do png. 
  1. SVG obrázky hľadá v `temp/img_exported_svg`. Pri exporte do svg hrá rolu parameter `poster [-p]`, ktorý hovorí aký veľký obrázok bude. Štandardne je density nastavená 144, poster je koeficient ktorým sa to vynásobí (napr. 3)
  2. Umlet, Mermaid obrázky hľadá v `src_doc/img`
  3. Všetky prekonvertuje do png a uloži do `temp/img_exported`
2. Doplnenie **icons** do obrázku
   1. Potrebuje k tomu súbor `src_doc/img/icons.json`, v ňom je popísané aké ikony doplniť do obrázkov
   2. Obrázky číta z adresára `temp/img_exported`
   3. Obrázky s doplnenými ikonamy dáva do adresára `temp/img_icons`   
   4. Aj tu hrá rolu `poster`, prenásobia sa ním veľkosti ikon
3. Vytvorenie **areas** do obrázku, niektoré časti sú zvýraznené, ostatné zašedené
   1. Potrebuje k tomu súbor `src_doc/img/areass.json`
   2. Obrázky číta z adresára `temp/img_icons`
   3. Obrázky s doplnenými ikonamy dáva do adresára `temp/img_areas`
4. Skombinovanie všektých obrázkov do jedného adresára, najprv tam dá zdrojové, potom ich prepíše obrázkami s ikonami (tie ktoré sú) a nakoniec pridá areas obrázky
5. Vymazanie všetkého

## Identifikácia obdĺžnikov

Táto časť je spoločná aj pre ikony aj pre oblasti
1. Obrázok sa skonvertuje do čiernobieleho, lebo tam sa veci ľahšie identifikujú. Tu sa môže nastaviť atribút `treshold`, že čo už je biele a čo ešte čierne
2. Potom sa hľadajú obdĺžniky, použijú sa tieto parametre:
   1. `corner` - ak je oblý roh (services), tak chýba, toto hovorí aký veľký roh môže chýbať
   2. `gap` - medzera menej ako toľkoto bodov sa nepovažuje za medzeru
   3. `segment` - čiara kratšia ako toto sa nepovažuje za čiaru
3. Pri hľadaní sa vytvárajú obrázky, kde sa doplnia identifikované obdĺžniky a ukladá ich do adresára `temp/img_rec`, musí byť zapnutý debug logging. Sú tu znázornené čísla obdĺžnikov

## Ikony

1. `x` môže nadobúdať hodnoty `left`, `center`, `right` alebo číslo. Ak je to číslo (zväčša od 0 po 1), tak určuje ako ďaleko sa ikona umiestni zľava doprava. Podobne je to pri `y`, akurát hodnoty sú `top`, `center`, `bottom`
2. Ak definícia ikony neobsahuje atribút `rec`, tak sa očakáva, že `x,y` budú konkrétne pixels, priamo sa preberú.

```json
[
    { "fileName": "00-HighLevel/01-Projekty.png", "corner": 17, "icons": [
        { "rec":  1, "x": "center", "y": 0.45, "size":  130, "iconName": "CSRU.png"},
        { "rec":  2, "x": "center", "y": 0.45, "size":  130, "iconName": "OverSi.png"},
        { "rec":  3, "x": "center", "y": 0.49, "size":  130, "iconName": "MyData.png"},
        { "rec":  4, "x": "center", "y": 0.38, "size":   60, "iconName": "CIP.png"},
        { "rec":  5, "x": "center", "y": 0.38, "size":   60, "iconName": "DI.png"}
    ]},
    { "fileName": "00-HighLevel/01-ValueProposition.png", "corner": 17, "gap": 20, "segment": 30, "treshold" : 150, "icons": [
        { "rec":  1, "x": "center", "y": 0.72, "size":  110, "iconName": "DXC_Miscellaneous_Icons/Business-Strategy/Business_Strategy_PersonCircle.svg"},
        { "rec":  2, "x": "center", "y": 0.74, "size":  100, "iconName": "DXC_Miscellaneous_Icons/Agile/Agile_Megaphone.svg"},
        { "rec":  3, "x":     0.50, "y": 0.70, "size":  100, "iconName": "DXC_Miscellaneous_Icons/Business-Strategy/Business_Strategy_Puzzle.svg"},
        { "rec":  4, "x": "center", "y": 0.70, "size":  100, "iconName": "DXC_Miscellaneous_Icons/AI/AI_CircuitBrain2.svg"},
        { "rec":  5, "x":     0.50, "y": 0.74, "size":  100, "iconName": "DXC_Miscellaneous_Icons/Business-Management/Business_Management_PersonCheckbox.svg"}
    ]},
    { "fileName": "01-Business/01-MOU-PoC.png", "treshold" : 135, "icons": [
        { "rec":  1, "x":     0.18, "y":     0.36, "size":  75, "iconName": "ArtIntel.png"},
        { "rec":  1, "x":     0.50, "y":     0.36, "size":  75, "iconName": "lifecycle.png"},
        { "rec":  1, "x":     0.18, "y":     0.80, "size":  75, "iconName": "insurance.png"},
        { "rec":  1, "x":     0.50, "y":     0.80, "size":  75, "iconName": "people_secure.png"},
        { "rec":  1, "x":     0.83, "y":     0.80, "size":  75, "iconName": "DesignThinking.png"}
    ]}
]
```

## Oblasti

1. `ext` sa pridá do názvu obrázku, na ktorom bude zvýraznená časť
2. Sú tri druhy vecí, ktoré tu robím:
   1. `rect-area` - zvýraznenie oblasti cez jednoduchý obdĺžnik
   2. `polygon` - zvýraznenie oblasti cez polygon
   3. `lines` - dokreslovanie čiar pre zvýrazňovanie tokov
3. Spoločné parametre
   1. `linecolor`, `linewidth` určuje farbu a šírku čiary, týka sa všetkých
4. Pre rect-area a polygon
   1. `border` je hodnota, ako veľmi sa ohraničujúca čiara odsadí od obdĺžnikov
   2. `opacity` ako veľmi je priesvitná ostatná časť
   3. polygon obsahuje ešte `points`. Najprv je číslo obdĺžnika a potom identifikácia jedného z jeho rohov **T**op, **B**ottom, **L**eft, **R**ight
   4. rect-area obsahuje `coordinates` čo je ľavý horný a pravý dolný obdĺžnik ktoré určia ohraničenie
5. Lines je zoznam čiar, každá s hrúbkou a farbou. 
   1. Obsahuje `points` ktoré definujú odkiaľ kam čiara ide. 
   2. Prvý hovorí o umiestnení začiatku. Najprv id obdĺžnika, potom poloha v rámci neho
   3. Druhý (a každý ďalší) hovorí, ktorým smerom (iba T/D/L/R takže kolmo), do ktorého obdĺžnika a tam pozícia v smere ktorý sa mení, druhá súradnica sa preberie. ```json [[rectID, x, y], [direction, rectID, position], [direction, rectID, position], ...```
   4. Ešte je tam `arrowsize` ktorá určuje či je na konci šípka a aká je veľká.
   5. Ešte je tam `circlesize` ktorá určuje či je na začiatku krúžok a aký veľký.

```json
[
    { "fileName": "02-Application/01-AA-functions.png", "ext":"01-obcan", 
        "rect-area": {"corners" : [1, 11]}
    },
    { "fileName": "02-Application/01-AA-functions.png", "ext":"11-nacitanie", 
        "rect-area": {"opacity" : 30, "linecolor" : [99,102,106], "corners" : [3, 12]},
        "lines": [
            {"linewidth": 6, "arrowsize":12, "points" : [[ 4, 0.2, 0.5], [3, "L", 0.5], [12, "D", 0.6]]}
        ]
    },
    { "fileName": "02-Application/01-AA-functions.png", "ext":"12-prezeranie", 
        "polygon": {"opacity" : 30, "linecolor" : [99,102,106], "points":[[1, "TL"], [2, "TR"], [12, "TL"], [12, "TR"], [12, "BR"], [2, "BL"], [7, "BR"], [7, "BL"]]},
        "lines": [
            {"linewidth": 6, "arrowsize":12, "points" : [[12, 0.2, 0.5], [2, "L", 0.5], [2, "U", 0.15], [1, "L", 0.5]]}
        ]
    },
    { "fileName": "02-Application/01-AA-functions.png", "ext":"15-adhoc-poskytnutie2", 
        "polygon": {"opacity" : 30, "linecolor" : [99,102,106], "points" : [[1, "TL"], [2, "TR"], [12, "TL"], [12, "TR"], [12, "BR"], [11, "BL"]]},
        "lines": [
            {"linewidth": 6, "arrowsize":12, "circlesize":12, "points" : [[7, 0.5, 0.3], [1, "U", 0.8], [2, "R", 0.2], [2, "D", 0.78], [11, "L", 0.8]]},
            {"linewidth": 6, "arrowsize":12, "points" : [[12, 0.1, 0.26], [2, "L", 0.8], [2, "U", 0.1], [1, "L", 0.25], [7, "D", 0.3]]},
            {"linewidth": 6, "arrowsize":12, "points" : [[2, 0.5, 0.85], [11, "L", 0.8]]}
        ]
    },
```
