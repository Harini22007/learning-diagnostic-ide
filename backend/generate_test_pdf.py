# Script to generate a valid test PDF file with study material text
import os

pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Resources << /Font << /F1 5 0 R >> >>
/Contents 6 0 R >>
endobj
4 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Resources << /Font << /F1 5 0 R >> >>
/Contents 7 0 R >>
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
6 0 obj
<< /Length 265 >>
stream
BT
/F1 16 Tf
50 720 Td
(Cellular Biology and Energy Systems) Tj
/F1 12 Tf
0 -30 Td
(Topic: Photosynthesis and Cellular Respiration) Tj
0 -25 Td
(Light Reactions take place in the thylakoid membranes.) Tj
0 -20 Td
(Chlorophyll absorbs solar photon energy to split water molecules.) Tj
0 -20 Td
(Calvin Cycle uses ATP and NADPH to fix carbon dioxide into glucose.) Tj
ET
endstream
endobj
7 0 obj
<< /Length 285 >>
stream
BT
/F1 14 Tf
50 720 Td
(Topic: Cellular Respiration & ATP Production) Tj
/F1 12 Tf
0 -25 Td
(Glycolysis breaks down glucose into pyruvate in the cytoplasm.) Tj
0 -20 Td
(Krebs Cycle produces electron carriers NADH and FADH2.) Tj
0 -20 Td
(Prerequisites: Basic Organic Chemistry, Enzymes.) Tj
0 -20 Td
(Electron Transport Chain drives ATP synthase across inner membrane.) Tj
ET
endstream
endobj
xref
0 8
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000228 00000 n 
0000000341 00000 n 
0000000412 00000 n 
0000000730 00000 n 
trailer
<< /Size 8 /Root 1 0 R >>
startxref
1068
%%EOF
"""

os.makedirs("test_materials", exist_ok=True)
with open("test_materials/sample_biology_notes.pdf", "wb") as f:
    f.write(pdf_content)

print("Generated test_materials/sample_biology_notes.pdf successfully.")
