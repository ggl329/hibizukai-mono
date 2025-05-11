# HibizukaiMono

HibizukaiMono は [BIZ UDゴシック](https://github.com/googlefonts/morisawa-biz-ud-gothic) と
[JetBrains Mono](https://github.com/JetBrains/JetBrainsMono)、
[Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) の合成フォントです。
[UDEV Gothic](https://github.com/yuru7/udev-gothic) を参考にして作成されています。

## UDEV Gothic との違い

HibizukaiMono は UDEV Gothic をベースとして、次のような調整をしています。

- UDEV Gothic のバリエーション
    - 半角1:全角2の文字幅比率
    - 日本語文書向け記号を全角化（例外として、U+2018-U+201F の QUOTE 系は JetBrains Mono の半角グリフを採用）
    - 全角スペース可視化は適用しない
    - リガチャ非対応
- [Bizin Gothic](https://github.com/yuru7/bizin-gothic) で採用されている半濁点の強調による判読性の向上
- BIZ UDゴシック由来の丸数字グリフを採用
- JetBrains Mono 由来の '■□●○' (U+25A0, U+25A1, U+25CF, U+25CB) を、
  '◼◻⚫⚪' (U+25FC, U+25FB, U+26AB, U+26AA) にコピー
- わずかに condensed 化
