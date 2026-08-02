"""Desenhos ASCII dos teclados usados no guia de posicionamento das mãos.

Cada layout é mostrado conforme o idioma escolhido, porque a posição das teclas muda:
o ABNT2 tem Ç e til/circunflexo à direita do L, o italiano tem ò/à/ù no mesmo lugar e
o US QWERTY tem ponto-e-vírgula e aspas. Treinar digitação com o desenho errado ensina
o dedo a ir para a tecla errada, daí valer um layout por idioma.

O `focused_keys_ascii_template` é o desenho reduzido, só da linha QWERTY, com marcações
`{...}` que o i18n preenche com os nomes dos dedos no idioma ativo (LP/LR/LM/LI em
inglês, MgS/AnS/MdS/InS em italiano, MnE/AnE/MdE/InE em português).
"""

abnt2_full_keyboard_ascii = """
+-----------------------------------------------------------------------------------+
| `~ | 1!| 2@| 3#| 4$| 5%| 6^| 7&| 8*| 9(| 0)| -_| =+| Backspace               |
| Tab |  Q|  W|  E|  R|  T|  Y|  U|  I|  O|  P|  ´`|  [{|          Enter        |
|CapsL|  A|  S|  D|  F|  G|  H|  J|  K|  L|  Ç|  ~^|  ]} |          |        |
|LShft|  Z|  X|  C|  V|  B|  N|  M|  ,<|  .>|  ;:| /?°|         RShift          |
|LCtrl|LWin|LAlt|                    Spacebar                     |RAltGr|Menu|RCtrl|
+-----------------------------------------------------------------------------------+
"""
us_qwerty_full_keyboard_ascii = """
+-----------------------------------------------------------------------------------+
| `~ | 1!| 2@| 3#| 4$| 5%| 6^| 7&| 8*| 9(| 0)| -_| =+| Backspace               |
| Tab |  Q|  W|  E|  R|  T|  Y|  U|  I|  O|  P|  [{|  ]}|         \\ |           |
|CapsL|  A|  S|  D|  F|  G|  H|  J|  K|  L|  ;:|  '"|          Enter            |
|LShft|  Z|  X|  C|  V|  B|  N|  M|  ,<|  .>|  /?|           RShift          |
|LCtrl|LWin|LAlt|                    Spacebar                     |RAlt|Menu|RCtrl|
+-----------------------------------------------------------------------------------+
"""
it_qwerty_full_keyboard_ascii = """
+-----------------------------------------------------------------------------------+
| \\| | 1!| 2"| 3£| 4$| 5%| 6&| 7/| 8(| 9)| 0=| ?'| ì^| Backspace               |
| Tab |  Q|  W|  E|  R|  T|  Y|  U|  I|  O|  P|  è*[|  é+]|         Invio         |
|CapsL|  A|  S|  D|  F|  G|  H|  J|  K|  L|  ò@|  à#|  ù§|                     |
|LShft|> <|  Z|  X|  C|  V|  B|  N|  M|  ;%|  :_|  -|           RShift          |
|LCtrl|LWin|LAlt|                    Spacebar                     |RAltGr|Menu|RCtrl|
+-----------------------------------------------------------------------------------+
"""

focused_keys_ascii_template = """
{line1}
      {left_hand_label}                           {right_hand_label}
      -------------------                     -----------------------
      | Q | W | E | R | T |         | Y | U | I | O | P | {key_right_of_p} |
      --- --- --- --- ---         --- --- --- --- --- -----
      |{L_P_key}|{L_R_key}|{L_M_key}|{L_I_key}|{L_I_key}|         |{R_I_key}|{R_I_key}|{R_M_key}|{R_R_key}|{R_P_key}| {R_P_Alt_key} |
      --- --- --- --- ---         --- --- --- --- --- -----
{line2}
{legend_title}
  {L_P_key_legend} = {pinky_label} ({left_label_short})        {R_P_key_legend} = {pinky_label} ({right_label_short})
  {L_R_key_legend} = {ring_label} ({left_label_short})       {R_R_key_legend} = {ring_label} ({right_label_short})
  {L_M_key_legend} = {middle_label} ({left_label_short})     {R_M_key_legend} = {middle_label} ({right_label_short})
  {L_I_key_legend} = {index_label} ({left_label_short})      {R_I_key_legend} = {index_label} ({right_label_short})

{thumbs_rest_label}
"""
