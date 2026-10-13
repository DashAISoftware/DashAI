"""Document dataloader for PDF files using pdfplumber."""

from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Tuple

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.document_blocks import (
    BLOCK_GRANULARITY,
    GRANULARITIES,
    name_blocks,
    representative_size,
)
from DashAI.back.dataloaders.classes.document_dataloader import (
    DocumentDataLoader,
    DocumentLoaderError,
)
from DashAI.back.dataloaders.classes.document_elements import table_text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_document import DashAIDocument


class PdfPlumberDocumentSchema(BaseSchema):
    """Parameters for PdfPlumberDocumentDataLoader."""

    password: schema_field(
        none_type(string_field()),
        placeholder=None,
        description=MultilingualString(
            en="Password for encrypted PDFs. Leave empty for unencrypted files.",
            es=("Contraseña para PDF cifrados. Déjala vacía para archivos sin cifrar."),
            pt=("Senha para PDF cifrados. Deixe vazia para arquivos sem cifragem."),
            de=(
                "Passwort für verschlüsselte PDFs. Für unverschlüsselte "
                "Dateien leer lassen."
            ),
            zh="加密 PDF 的密码。未加密文件请留空。",
        ),
        alias=MultilingualString(
            en="Password",
            es="Contraseña",
            pt="Senha",
            de="Passwort",
            zh="密码",
        ),
    )  # type: ignore
    x_tolerance: schema_field(
        float_field(gt=0.0),
        placeholder=3.0,
        description=MultilingualString(
            en=(
                "Horizontal distance, in points, below which two characters "
                "belong to the same word. Lower it when words run together."
            ),
            es=(
                "Distancia horizontal, en puntos, por debajo de la cual dos "
                "caracteres pertenecen a la misma palabra. Redúcela cuando las "
                "palabras se peguen entre sí."
            ),
            pt=(
                "Distância horizontal, em pontos, abaixo da qual dois "
                "caracteres pertencem à mesma palavra. Reduza quando as "
                "palavras ficarem coladas."
            ),
            de=(
                "Waagerechter Abstand in Punkt, unter dem zwei Zeichen zum "
                "selben Wort gehören. Verringern, wenn Wörter zusammenlaufen."
            ),
            zh=(
                "以点为单位的水平距离，小于该值的两个字符属于同一个词。"
                "单词粘连时可减小该值。"
            ),
        ),
        alias=MultilingualString(
            en="Horizontal tolerance",
            es="Tolerancia horizontal",
            pt="Tolerância horizontal",
            de="Waagerechte Toleranz",
            zh="水平容差",
        ),
    )  # type: ignore
    y_tolerance: schema_field(
        float_field(gt=0.0),
        placeholder=3.0,
        description=MultilingualString(
            en=(
                "Vertical distance, in points, below which two characters "
                "belong to the same line. Raise it when a line is split in two."
            ),
            es=(
                "Distancia vertical, en puntos, por debajo de la cual dos "
                "caracteres pertenecen a la misma línea. Auméntala cuando una "
                "línea se parta en dos."
            ),
            pt=(
                "Distância vertical, em pontos, abaixo da qual dois caracteres "
                "pertencem à mesma linha. Aumente quando uma linha se partir "
                "em duas."
            ),
            de=(
                "Senkrechter Abstand in Punkt, unter dem zwei Zeichen zur "
                "selben Zeile gehören. Erhöhen, wenn eine Zeile in zwei "
                "geteilt wird."
            ),
            zh=(
                "以点为单位的垂直距离，小于该值的两个字符属于同一行。"
                "一行被拆成两行时可增大该值。"
            ),
        ),
        alias=MultilingualString(
            en="Vertical tolerance",
            es="Tolerancia vertical",
            pt="Tolerância vertical",
            de="Senkrechte Toleranz",
            zh="垂直容差",
        ),
    )  # type: ignore
    layout: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en=(
                "Pad the output with whitespace so it mirrors the position of "
                "the text on the page. Preserves columns at the cost of extra "
                "whitespace."
            ),
            es=(
                "Rellena la salida con espacios para que refleje la posición "
                "del texto en la página. Conserva las columnas a costa de "
                "espacios adicionales."
            ),
            pt=(
                "Preenche a saída com espaços para refletir a posição do texto "
                "na página. Preserva as colunas ao custo de espaços extras."
            ),
            de=(
                "Füllt die Ausgabe mit Leerzeichen, sodass sie die Position "
                "des Textes auf der Seite widerspiegelt. Erhält Spalten auf "
                "Kosten zusätzlicher Leerzeichen."
            ),
            zh=(
                "用空白填充输出，使其还原文本在页面上的位置。"
                "可保留分栏，代价是多出空白字符。"
            ),
        ),
        alias=MultilingualString(
            en="Preserve layout",
            es="Conservar el diseño",
            pt="Preservar o layout",
            de="Layout erhalten",
            zh="保留版面",
        ),
    )  # type: ignore
    extract_tables: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en=(
                "Store each detected table as its own text item of tab "
                "separated rows, right after the text of its page."
            ),
            es=(
                "Guarda cada tabla detectada como su propio elemento de texto "
                "con filas separadas por tabuladores, justo después del texto "
                "de su página."
            ),
            pt=(
                "Guarda cada tabela detectada como seu próprio item de texto "
                "com linhas separadas por tabulações, logo após o texto da sua "
                "página."
            ),
            de=(
                "Speichert jede erkannte Tabelle als eigenes Textelement mit "
                "tabulatorgetrennten Zeilen, direkt nach dem Text ihrer Seite."
            ),
            zh=(
                "将识别出的每个表格保存为独立的文本项，行以制表符分隔，"
                "紧随该页文本之后。"
            ),
        ),
        alias=MultilingualString(
            en="Extract tables",
            es="Extraer tablas",
            pt="Extrair tabelas",
            de="Tabellen extrahieren",
            zh="提取表格",
        ),
    )  # type: ignore
    granularity: schema_field(
        enum_field(GRANULARITIES),
        placeholder=BLOCK_GRANULARITY,
        description=MultilingualString(
            en=(
                "How much text one item holds. One item per block groups the "
                "lines of a page into blocks and stores each one on its own; "
                "one item per page keeps the whole page together. A block "
                "never crosses a page boundary."
            ),
            es=(
                "Cuánto texto guarda un elemento. Un elemento por bloque "
                "agrupa las líneas de una página en bloques y guarda cada uno "
                "por separado; un elemento por página mantiene la página "
                "completa. Un bloque nunca cruza el límite de una página."
            ),
            pt=(
                "Quanto texto um item guarda. Um item por bloco agrupa as "
                "linhas de uma página em blocos e guarda cada um "
                "separadamente; um item por página mantém a página inteira. Um "
                "bloco nunca cruza o limite de uma página."
            ),
            de=(
                "Wie viel Text ein Element enthält. Ein Element pro Block "
                "gruppiert die Zeilen einer Seite zu Blöcken und speichert "
                "jeden einzeln; ein Element pro Seite behält die ganze Seite "
                "zusammen. Ein Block überschreitet nie eine Seitengrenze."
            ),
            zh=(
                "一个项包含多少文本。每个文本块一个项会把页面中的行分组为"
                "文本块并分别保存；每页一个项则保留整页。文本块不会跨页。"
            ),
        ),
        alias=MultilingualString(
            en="Granularity",
            es="Granularidad",
            pt="Granularidade",
            de="Granularität",
            zh="粒度",
        ),
    )  # type: ignore
    block_gap: schema_field(
        float_field(gt=0.0),
        placeholder=0.6,
        description=MultilingualString(
            en=(
                "Vertical gap between two lines, as a fraction of line height, "
                "above which a new block starts. Raise it to join lines that "
                "sit far apart. Only used when one item holds one block."
            ),
            es=(
                "Separación vertical entre dos líneas, como fracción de la "
                "altura de línea, por encima de la cual empieza un bloque "
                "nuevo. Auméntala para unir líneas muy separadas. Solo se usa "
                "cuando un elemento guarda un bloque."
            ),
            pt=(
                "Espaço vertical entre duas linhas, como fração da altura da "
                "linha, acima do qual começa um bloco novo. Aumente para "
                "juntar linhas muito distantes. Usado apenas quando um item "
                "guarda um bloco."
            ),
            de=(
                "Senkrechter Abstand zwischen zwei Zeilen als Anteil der "
                "Zeilenhöhe, über dem ein neuer Block beginnt. Erhöhen, um "
                "weit auseinander liegende Zeilen zu verbinden. Nur wirksam, "
                "wenn ein Element einen Block enthält."
            ),
            zh=(
                "以行高为单位的两行间垂直间距，超过该值则开始新的文本块。"
                "行距很大时可增大该值以合并。仅在一个项包含一个文本块时生效。"
            ),
        ),
        alias=MultilingualString(
            en="Block gap",
            es="Separación de bloque",
            pt="Espaço de bloco",
            de="Blockabstand",
            zh="文本块间距",
        ),
    )  # type: ignore
    detect_headings: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=(
                "Name short blocks set in a font larger than the body text as "
                "headings, with a level from the rank of their size. Only used "
                "when one item holds one block."
            ),
            es=(
                "Nombra como títulos los bloques cortos con una fuente mayor "
                "que el texto del cuerpo, con un nivel según el rango de su "
                "tamaño. Solo se usa cuando un elemento guarda un bloque."
            ),
            pt=(
                "Nomeia como títulos os blocos curtos com uma fonte maior que "
                "o texto do corpo, com um nível conforme a posição do seu "
                "tamanho. Usado apenas quando um item guarda um bloco."
            ),
            de=(
                "Benennt kurze Blöcke in einer größeren Schrift als der "
                "Fließtext als Überschriften, mit einer Ebene nach dem Rang "
                "ihrer Größe. Nur wirksam, wenn ein Element einen Block "
                "enthält."
            ),
            zh=(
                "将字号大于正文的短文本块命名为标题，级别取决于其字号的排名。"
                "仅在一个项包含一个文本块时生效。"
            ),
        ),
        alias=MultilingualString(
            en="Detect headings",
            es="Detectar títulos",
            pt="Detectar títulos",
            de="Überschriften erkennen",
            zh="识别标题",
        ),
    )  # type: ignore


class PdfPlumberDocumentDataLoader(DocumentDataLoader):
    """Parse a PDF with pdfplumber: per page, its text blocks, then its tables.

    With 'block' granularity the lines of a page are grouped into blocks by
    the gap between them and by their font size, and a short block set larger
    than the body text is named a heading. With 'page' granularity the text
    of a page becomes one item.
    """

    SCHEMA: ClassVar[BaseSchema] = PdfPlumberDocumentSchema
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})
    DISPLAY_NAME = MultilingualString(
        en="pdfplumber",
        es="pdfplumber",
        pt="pdfplumber",
        de="pdfplumber",
        zh="pdfplumber",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Reads PDF files with pdfplumber, which detects words and tables. "
            "Groups the lines of a page into blocks and stores each one as a "
            "text item, or keeps the whole page as a single item, and when "
            "enabled stores each detected table as a separate text item of tab "
            "separated rows."
        ),
        es=(
            "Lee archivos PDF con pdfplumber, que detecta palabras y tablas. "
            "Agrupa las líneas de una página en bloques y guarda cada uno como "
            "un elemento de texto, o conserva la página completa como un único "
            "elemento, y si se activa guarda cada tabla detectada como otro "
            "elemento de texto con filas separadas por tabuladores."
        ),
        pt=(
            "Lê arquivos PDF com pdfplumber, que detecta palavras e tabelas. "
            "Agrupa as linhas de uma página em blocos e guarda cada um como um "
            "item de texto, ou mantém a página inteira como um único item, e "
            "quando ativado guarda cada tabela detectada como outro item de "
            "texto com linhas separadas por tabulações."
        ),
        de=(
            "Liest PDF-Dateien mit pdfplumber, das Wörter und Tabellen erkennt. "
            "Gruppiert die Zeilen einer Seite zu Blöcken und speichert jeden "
            "als Textelement, oder behält die ganze Seite als ein einziges "
            "Element, und speichert, falls aktiviert, jede erkannte Tabelle als "
            "eigenes Textelement mit tabulatorgetrennten Zeilen."
        ),
        zh=(
            "使用 pdfplumber 读取 PDF 文件，可识别单词和表格。将页面中的行分组为"
            "文本块并分别保存为文本项，或整页保存为一个文本项；启用后，"
            "每个识别出的表格会另存为以制表符分隔行的文本项。"
        ),
    )

    @classmethod
    def render_table(cls, table: List[List[object]]) -> str:
        """Render one table as tab separated rows.

        Parameters
        ----------
        table : List[List[object]]
            Rows of cells as pdfplumber returns them; empty cells are None.

        Returns
        -------
        str
            Newline separated rows of tab separated cells.
        """
        return table_text(cls.table_rows(table))

    @staticmethod
    def table_rows(table: List[List[object]]) -> List[List[str]]:
        """Turn one pdfplumber table into rows of string cells.

        Parameters
        ----------
        table : List[List[object]]
            Rows of cells as pdfplumber returns them; empty cells are None.

        Returns
        -------
        List[List[str]]
            The same rows with every cell as a string, empty cells as "".
        """
        return [[str(cell) if cell else "" for cell in row] for row in table]

    @staticmethod
    def _line_sizes(line: Dict[str, Any]) -> List[float]:
        """Return the font size of every character of one extracted line."""
        return [char["size"] for char in line.get("chars") or [] if char.get("size")]

    @classmethod
    def _starts_block(
        cls,
        previous: Dict[str, Any],
        line: Dict[str, Any],
        block_gap: float,
    ) -> bool:
        """Tell whether a line opens a new block instead of continuing one.

        A line starts a block when it sits further below the previous line
        than ``block_gap`` line heights, or when its font size differs, which
        is what separates a heading from the paragraph under it.

        Parameters
        ----------
        previous : Dict[str, Any]
            The line above, as ``extract_text_lines`` returns it.
        line : Dict[str, Any]
            The line being placed.
        block_gap : float
            Gap above which a new block starts, in line heights.

        Returns
        -------
        bool
            True when ``line`` opens a new block.
        """
        height = max(previous["bottom"] - previous["top"], 1e-6)
        if line["top"] - previous["bottom"] > block_gap * height:
            return True
        before = representative_size(cls._line_sizes(previous))
        current = representative_size(cls._line_sizes(line))
        return before is not None and current is not None and before != current

    @classmethod
    def _group_lines(
        cls, lines: List[Dict[str, Any]], block_gap: float
    ) -> List[Tuple[str, Optional[float]]]:
        """Group the lines of a page into blocks.

        Parameters
        ----------
        lines : List[Dict[str, Any]]
            The lines of one page, as ``extract_text_lines`` returns them.
        block_gap : float
            Gap above which a new block starts, in line heights.

        Returns
        -------
        List[Tuple[str, Optional[float]]]
            Each block as its newline joined text and its font size, in
            reading order.
        """
        blocks: List[Tuple[str, Optional[float]]] = []
        texts: List[str] = []
        sizes: List[float] = []
        previous = None
        for line in lines:
            text = (line.get("text") or "").strip()
            if not text:
                continue
            if previous is not None and cls._starts_block(previous, line, block_gap):
                blocks.append(("\n".join(texts), representative_size(sizes)))
                texts, sizes = [], []
            texts.append(text)
            sizes.extend(cls._line_sizes(line))
            previous = line
        if texts:
            blocks.append(("\n".join(texts), representative_size(sizes)))
        return blocks

    def _page_text_parts(
        self, page: Any, params: Dict[str, Any]
    ) -> List[Tuple[str, Optional[float]]]:
        """Return the text blocks of one page, honouring the granularity."""
        if params["granularity"] == BLOCK_GRANULARITY:
            lines = page.extract_text_lines(
                x_tolerance=params["x_tolerance"],
                y_tolerance=params["y_tolerance"],
                layout=params["layout"],
            )
            return self._group_lines(lines, params["block_gap"])
        text = page.extract_text(
            x_tolerance=params["x_tolerance"],
            y_tolerance=params["y_tolerance"],
            layout=params["layout"],
        )
        return [(text.strip(), None)] if text and text.strip() else []

    def _read_pages(self, file_path: str, params: Dict[str, Any]) -> List[List[Any]]:
        """Read the text parts of every page.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            Resolved parameters.

        Returns
        -------
        List[List[Any]]
            Per page: each text block as a ``(text, font size)`` tuple, then
            each non blank table as its raw rows (a list).
        """
        import pdfplumber

        pages = []
        with pdfplumber.open(file_path, password=params["password"] or "") as pdf:
            for page in pdf.pages:
                parts: List[Any] = list(self._page_text_parts(page, params))
                if params["extract_tables"]:
                    for table in page.extract_tables():
                        if self.render_table(table).strip():
                            parts.append(table)
                pages.append(parts)
        return pages

    def load_document(self, file_path: str, params: Dict[str, Any]) -> "DashAIDocument":
        """Parse a PDF with pdfplumber.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            pdfplumber parameters, ``granularity``, ``block_gap`` and
            ``detect_headings``; missing keys take the defaults.

        Returns
        -------
        DashAIDocument
            Text items for the blocks of each page, named as headings when
            they stand out, and table items with their rows, in reading
            order.

        Raises
        ------
        DocumentLoaderError
            If pdfplumber cannot read the file.
        """
        from DashAI.back.dataloaders.classes.dashai_document import (
            DashAIDocument,
            DocumentItem,
        )
        from DashAI.back.types.value_types import Text

        resolved = self.resolve_params(params)
        try:
            pages = self._read_pages(file_path, resolved)
        except Exception as e:
            raise DocumentLoaderError(
                f"pdfplumber failed to read {file_path}: {e}"
            ) from e
        flat = [
            (number, part)
            for number, parts in enumerate(pages, start=1)
            for part in parts
        ]
        texts = [part for _, part in flat if isinstance(part, tuple)]
        named = (
            name_blocks(texts)
            if resolved["granularity"] == BLOCK_GRANULARITY
            and resolved["detect_headings"]
            else [("paragraph", {})] * len(texts)
        )
        elements = iter(named)
        items = []
        for number, part in flat:
            if isinstance(part, tuple):
                kind, attrs = next(elements)
                items.append(
                    DocumentItem(
                        type=Text,
                        content=part[0],
                        page=number,
                        kind=kind,
                        attrs=attrs,
                    )
                )
                continue
            items.append(
                DocumentItem(
                    type=Text,
                    content=self.render_table(part),
                    page=number,
                    kind="table",
                    attrs={"rows": self.table_rows(part)},
                )
            )
        return DashAIDocument.from_items(
            items, metadata=self.build_metadata(file_path, resolved, len(pages))
        )
