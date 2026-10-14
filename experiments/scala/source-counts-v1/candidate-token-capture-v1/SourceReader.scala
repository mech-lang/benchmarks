// Source-only draft for scala/scala3 25c18aaa21b6be202945e024cd5180d9d62d650f.
// Not compiled or run. This transports parser evidence; it does not count LOC.
package benchmark.scala310tokencapture

import java.nio.ByteBuffer
import java.nio.charset.{CodingErrorAction, StandardCharsets}
import java.nio.file.{Files, Path, StandardOpenOption}
import java.security.MessageDigest
import java.util.{Base64, IdentityHashMap}
import scala.collection.mutable.ArrayBuffer
import scala.util.control.NonFatal
import dotty.tools.dotc.CompilationUnit
import dotty.tools.dotc.ast.{Positioned, Trees, untpd}
import dotty.tools.dotc.ast.Trees.mods
import dotty.tools.dotc.core.Contexts.{Context, ContextBase}
import dotty.tools.dotc.core.Constants.Constant
import dotty.tools.dotc.core.Flags.*
import dotty.tools.dotc.core.Names.{Name, SimpleName}
import dotty.tools.dotc.parsing.Parsers.Parser
import dotty.tools.dotc.parsing.Scanners.{Scanner, TokenData}
import dotty.tools.dotc.parsing.Tokens.*
import dotty.tools.dotc.core.Comments.Comment
import dotty.tools.dotc.reporting.{Diagnostic, Profile, StoreReporter}
import dotty.tools.dotc.util.{SourceFile, SourcePosition}
import dotty.tools.dotc.util.Spans.Span

object SourceReader:
  private val expectedCommit = "25c18aaa21b6be202945e024cd5180d9d62d650f"

  // JSON escaping works on UTF-16 code units, including surrogate pairs.
  private def quote(s: String): String =
    val b = new StringBuilder("\"")
    s.foreach { c =>
      if c == '"' then b.append("\\\"")
      else if c == '\\' then b.append("\\\\")
      else if c < ' ' || c > '~' then b.append(f"\\u${c.toInt}%04x")
      else b.append(c)
    }
    b.append('"').toString

  private def obj(fields: (String, String)*): String =
    fields.map((k, v) => quote(k) + ":" + v).mkString("{", ",", "}")
  private def arr(xs: scala.collection.Iterable[String]): String = xs.mkString("[", ",", "]")
  private def bool(b: Boolean): String = b.toString

  private def span(s: Span): String =
    if !s.exists then obj("coords" -> quote(s.coords.toString), "exists" -> "false")
    else obj("coords" -> quote(s.coords.toString), "exists" -> "true",
      "start" -> s.start.toString, "end" -> s.end.toString, "point" -> s.point.toString,
      "synthetic" -> bool(s.isSynthetic), "source_derived" -> bool(s.isSourceDerived),
      "zero_extent" -> bool(s.isZeroExtent))

  private def position(p: SourcePosition): String =
    obj("source" -> quote(p.source.path), "source_exists" -> bool(p.source.exists),
      "span" -> span(p.span),
      "outer" -> (if p.outer == null then "null" else position(p.outer)))

  // Preserve incoming diagnostics before stock warning suppression/summarization.
  // super.report retains the compiler's ordinary error counters and recovery behavior.
  private final class CaptureReporter extends StoreReporter:
    val incoming = ArrayBuffer.empty[Diagnostic]
    override def report(d: Diagnostic)(using Context): Unit =
      incoming += d
      super.report(d)

  private def diagnostic(d: Diagnostic): String =
    obj("class" -> quote(d.getClass.getName), "message_class" -> quote(d.msg.getClass.getName),
      "level" -> d.level.toString, "message" -> quote(d.message), "position" -> position(d.pos))

  // Graph IDs use reference identity, not Positioned.uniqueId (normally -1).
  // Product roles are native field names. Edges are structural references, not
  // assertions that a node owns authored source or has exactly one parent.
  private final class Graph(inputSource: SourceFile)(using Context):
    private val ids = new IdentityHashMap[Positioned, Integer]()
    private val sources = new IdentityHashMap[SourceFile, Integer]()
    val nodes = ArrayBuffer.empty[String]
    val edges = ArrayBuffer.empty[String]
    val sourceRecords = ArrayBuffer.empty[String]
    val problems = ArrayBuffer.empty[String]

    private def sourceId(s: SourceFile): Int =
      val old = sources.get(s)
      if old != null then old.intValue
      else
        val id = sources.size()
        sources.put(s, Integer.valueOf(id))
        sourceRecords += obj("id" -> id.toString, "path" -> quote(s.path),
          "exists" -> bool(s.exists), "is_input_source" -> bool(s eq inputSource))
        id

    private def opaque(v: Any, parent: Int, role: String): String =
      val cls = v.getClass.getName
      problems += obj("kind" -> quote("unexpanded_native_value"),
        "parent" -> parent.toString, "role" -> quote(role), "class" -> quote(cls))
      obj("kind" -> quote("opaque"), "class" -> quote(cls))

    private def value(v: Any, parent: Int, role: String): String = v match
      case null => "null"
      case p: Positioned =>
        val child = node(p)
        edges += obj("parent" -> parent.toString, "role" -> quote(role), "child" -> child.toString)
        obj("node" -> child.toString)
      case m: untpd.Modifiers =>
        obj("kind" -> quote("Modifiers"), "flags_bits" -> quote(m.flags.bits.toString),
          "private_within" -> quote(m.privateWithin.toString),
          "mods" -> value(m.mods, parent, role + ".mods"),
          "annotations" -> value(m.annotations, parent, role + ".annotations"))
      case xs: List[?] => arr(xs.zipWithIndex.map((x, i) => value(x, parent, s"$role[$i]")))
      case n: Name => obj("kind" -> quote("Name"), "class" -> quote(n.getClass.getName),
        "text" -> quote(n.toString))
      case c: Constant => obj("kind" -> quote("Constant"), "tag" -> c.tag.toString,
        "value" -> value(c.value, parent, role + ".value"))
      case untpd.NumberKind.Whole(radix) => obj("kind" -> quote("NumberKind"),
        "case" -> quote("Whole"), "radix" -> radix.toString)
      case untpd.NumberKind.Decimal => obj("kind" -> quote("NumberKind"), "case" -> quote("Decimal"))
      case untpd.NumberKind.Floating => obj("kind" -> quote("NumberKind"), "case" -> quote("Floating"))
      case g: untpd.GenCheckMode => obj("kind" -> quote("GenCheckMode"),
        "case" -> quote(g.toString), "ordinal" -> g.ordinal.toString)
      case s: String => quote(s)
      case c: Char => obj("kind" -> quote("Char"), "code_unit" -> c.toInt.toString)
      case b: Boolean => bool(b)
      case n: java.lang.Number => obj("kind" -> quote("Number"),
        "class" -> quote(n.getClass.getName), "text" -> quote(n.toString))
      case () => obj("kind" -> quote("Unit"))
      // In particular, never force a LazyTree/typed field or invoke a getter
      // that might run a compiler phase. An unexpected container is explicit.
      case other => opaque(other, parent, role)

    def node(p: Positioned): Int =
      val old = ids.get(p)
      if old != null then old.intValue
      else
        val id = nodes.size
        ids.put(p, Integer.valueOf(id))
        nodes += "null" // Register before descendants, preserving sharing/cycles.
        val fields = (0 until p.productArity).map { i =>
          val role = p.productElementName(i)
          obj("role" -> quote(role), "value" -> value(p.productElement(i), id, role))
        }
        val extraModifiers = p match
          case d: untpd.DefTree => value(d.mods, id, "@modifiers")
          case f: untpd.FunctionWithMods => value(f.mods, id, "@modifiers")
          case _ => "null"
        val treeState = p match
          case t: untpd.Tree =>
            val nativeEmptyValDef = t eq untpd.EmptyValDef
            if t.hasType && !nativeEmptyValDef then
              problems += obj("kind" -> quote("typed_tree_in_parse_output"), "node" -> id.toString)
            obj("empty" -> bool(t.isEmpty), "has_type" -> bool(t.hasType),
              "native_empty_valdef_sentinel" -> bool(nativeEmptyValDef))
          case _ => "null"
        val endMarker = p match
          // endSpan -> srcName may consult symbol. With no type its native
          // denotation is NoDenotation; never use this on unexpected typed data.
          case e: Trees.WithEndMarker[?] => p match
            case t: untpd.Tree if !t.hasType => span(e.endSpan)
            case _ => "null"
          case _ => "null"
        val derived = p match
          // The inherited Template Product retains the combined parents list,
          // while this eager val preserves the otherwise missing derives split.
          case d: untpd.DerivingTemplate => value(d.derived, id, "@derived")
          case _ => "null"
        val modifierFlags = p match
          case m: untpd.Mod => quote(m.flags.bits.toString)
          case _ => "null"
        nodes(id) = obj("id" -> id.toString, "class" -> quote(p.getClass.getName),
          "product" -> quote(p.productPrefix), "source_id" -> sourceId(p.source).toString,
          "span" -> span(p.span), "tree_state" -> treeState,
          "native_definition_end_name_span" -> endMarker,
          "native_derived" -> derived,
          "native_modifier_flags_bits" -> modifierFlags,
          "fields" -> arr(fields), "extra_modifiers" -> extraModifiers,
          "authored_ownership_reviewed" -> "false")
        id

  // Installed before constructing ObservedScanner: Scanner's constructor calls
  // virtual nextToken before fields of the subclass have been initialized.
  private val activeCapture = new ThreadLocal[Capture]()

  private def tokenState(t: TokenData): String =
    obj("token" -> t.token.toString, "token_name" -> quote(showTokenDetailed(t.token)),
      "offset" -> t.offset.toString, "previous_token_end" -> t.lastOffset.toString,
      "line_offset" -> t.lineOffset.toString,
      "name" -> (if t.name == null then "null" else quote(t.name.toString)),
      "native_str_val" -> (if t.strVal == null then "null" else quote(t.strVal)),
      "base" -> t.base.toString, "delimiter" -> t.delimChar.toInt.toString,
      "delimiter_count" -> t.delimCount.toString)

  private def scannerState(s: Scanner): String =
    obj("current" -> tokenState(s), "buffered_next" -> tokenState(s.next),
      "char_offset" -> s.charOffset.toString, "last_char_offset" -> s.lastCharOffset.toString,
      "region_class" -> quote(s.currentRegion.getClass.getName))

  private final class FetchFrame(val method: String, val fresh: Boolean):
    var captured = false

  private case class PhysicalPiece(kind: String, token: Int, start: Int, end: Int,
      provenance: String, nativeState: String)

  private final class Capture(val text: String):
    val events = ArrayBuffer.empty[String]
    val issues = ArrayBuffer.empty[String]
    private val frames = ArrayBuffer.empty[FetchFrame]
    private val pieces = ArrayBuffer.empty[PhysicalPiece]
    private var observedEOF = false
    private var observedXML = false

    def issue(kind: String, detail: String): Unit =
      issues += obj("kind" -> quote(kind), "detail" -> quote(detail))

    def event(method: String, phase: String, s: Scanner, result: String = "null"): Unit =
      events += obj("sequence" -> events.size.toString, "method" -> quote(method),
        "phase" -> quote(phase), "state" -> scannerState(s), "result" -> result)

    def begin(method: String, s: Scanner): FetchFrame =
      val f = new FetchFrame(method, s.next.token == EMPTY)
      frames += f
      event(method, "before", s)
      f

    def end(f: FetchFrame, s: Scanner): Unit =
      event(f.method, "after", s)
      if f.fresh && !f.captured then issue("fresh_fetch_not_observed", f.method)
      if frames.nonEmpty && (frames.last eq f) then frames.remove(frames.size - 1)
      else issue("observer_frame_mismatch", f.method)

    private def add(token: Int, start: Int, end: Int, provenance: String, state: String): Unit =
      if token == XMLSTART then observedXML = true
      if token == ERROR || token == EMPTY then issue("invalid_physical_token", token.toString)
      pieces += PhysicalPiece("token", token, start, end, provenance, state)

    def capture(f: FetchFrame, s: Scanner, hook: String): Unit =
      if f.fresh && !f.captured then
        f.captured = true
        event(f.method, "fresh-lexical-result:" + hook, s)
        if s.token == EOF then
          observedEOF = true
          if s.lastCharOffset != text.length then
            issue("eof_before_source_end", s.lastCharOffset.toString)
        else if s.token == STRINGPART && s.next.token != EMPTY then
          // getStringPart consumes the following $identifier into next. Its
          // offset is an explicit native split; lastCharOffset ends that token.
          add(s.token, s.offset, s.next.offset, "interpolation-part-before-prefetched-token", tokenState(s))
          add(s.next.token, s.next.offset, s.lastCharOffset, "prefetched-interpolation-token", tokenState(s.next))
        else
          if s.next.token != EMPTY then issue("unexpected_buffer_created_by_lexical_fetch", hook)
          add(s.token, s.offset, s.lastCharOffset, "fresh-lexical-return:" + hook, tokenState(s))

    def captureNext(s: Scanner, hook: String): Unit =
      frames.lastOption match
        case Some(f) if f.method == "nextToken" => capture(f, s, hook)
        case _ => issue("lexical_hook_without_next_token_frame", hook)

    def around[A](method: String, s: Scanner)(op: => A): A =
      event(method, "before", s)
      try op finally event(method, "after", s)

    private def isBoundary(i: Int): Boolean =
      i >= 0 && i <= text.length &&
        !(i > 0 && i < text.length && Character.isHighSurrogate(text.charAt(i - 1)) &&
          Character.isLowSurrogate(text.charAt(i)))

    private def sourceSlice(start: Int, end: Int): String =
      if start >= 0 && end >= start && end <= text.length then quote(text.substring(start, end)) else "null"

    // Call once, after parsing. Native comment spans are preserved unchanged;
    // a distinct physical span accounts for the native CRLF lookahead overhang.
    def finish(comments: List[Comment], parseClean: Boolean, parity: Boolean,
        graphClean: Boolean, endedAtEOF: Boolean): (String, Boolean) =
      val commentRecords = comments.zipWithIndex.map { (c, index) =>
        if !c.span.exists then
          issue("comment_without_span", index.toString)
          obj("native_span" -> span(c.span), "native_raw" -> quote(c.raw))
        else
          val start = c.span.start
          val nativeEnd = c.span.end
          val crlfOverhang = nativeEnd > 0 && nativeEnd > start && nativeEnd < text.length &&
            text.charAt(nativeEnd - 1) == '\r' && text.charAt(nativeEnd) == '\n'
          val end = nativeEnd - (if crlfOverhang then 1 else 0)
          if start >= 0 && end >= start && end <= text.length then
            if text.substring(start, end).replace("\r\n", "\n") != c.raw then
              issue("native_comment_text_mismatch", index.toString)
          else issue("comment_out_of_bounds", index.toString)
          pieces += PhysicalPiece("comment", -1, start, end, "native-comment-span", "null")
          obj("index" -> index.toString, "native_span" -> span(c.span), "native_raw" -> quote(c.raw),
            "physical_start" -> start.toString, "physical_end" -> end.toString,
            "crlf_lookahead_overhang_removed" -> bool(crlfOverhang))
      }
      if frames.nonEmpty then issue("unclosed_observer_frames", frames.size.toString)
      if !observedEOF || !endedAtEOF then issue("missing_final_eof", "Parser/scanner did not establish EOF")
      if observedXML then issue("unsupported_xml_character_reader", "XML reads source outside token hooks")
      if !parseClean then issue("native_parse_not_clean", "Errors or exceptions prevent coverage admission")
      if !parity then issue("stock_parser_parity_failed", "Exact native transport differs")
      if !graphClean then issue("native_graph_not_complete", "Transport contains unsupported native data")

      val ordered = pieces.sortBy(p => (p.start, p.end))
      val whitespace = ArrayBuffer.empty[String]
      var cursor = 0
      def gap(to: Int): Unit =
        if to > cursor then
          val from = cursor
          var i = from
          var allWhitespace = true
          while i < to do
            // Exactly the whitespace cases in native fetchToken; no lexer is
            // substituted for strings, comments, keywords or punctuation.
            if !" \t\r\n\f".contains(text.charAt(i)) then allWhitespace = false
            i += 1
          if allWhitespace then whitespace += obj("start" -> from.toString, "end" -> to.toString,
            "text" -> quote(text.substring(from, to)))
          else issue("unexplained_source_gap", s"$from:$to")
      ordered.foreach { p =>
        if p.start < 0 || p.end <= p.start || p.end > text.length then
          issue("invalid_physical_interval", s"${p.kind}:${p.start}:${p.end}")
        else
          if !isBoundary(p.start) || !isBoundary(p.end) then
            issue("interval_splits_surrogate_pair", s"${p.start}:${p.end}")
          if p.start < cursor then issue("overlapping_physical_intervals", s"${p.start}:$cursor")
          else gap(p.start)
          cursor = math.max(cursor, p.end)
      }
      if cursor < text.length then gap(text.length)
      val complete = issues.isEmpty
      val records = pieces.zipWithIndex.map { (p, i) =>
        obj("id" -> i.toString, "kind" -> quote(p.kind), "token" -> p.token.toString,
          "token_name" -> (if p.token < 0 then "null" else quote(showTokenDetailed(p.token))),
          "start" -> p.start.toString, "end" -> p.end.toString,
          "source_text" -> sourceSlice(p.start, p.end), "provenance" -> quote(p.provenance),
          "native_state" -> p.nativeState)
      }
      (obj("events" -> arr(events), "physical_pieces" -> arr(records),
        "native_comments_with_physical_bounds" -> arr(commentRecords),
        "whitespace_intervals" -> arr(whitespace), "issues" -> arr(issues),
        "candidate_coverage_complete" -> bool(complete)), complete)

  private final class ObservedScanner(source: SourceFile)(using Context)
      extends Scanner(source, profile = Profile.current):
    private def capture: Capture =
      val c = activeCapture.get()
      require(c != null, "observer recorder must exist before scanner construction")
      c

    override def nextToken(): Unit =
      val c = capture
      val f = c.begin("nextToken", this)
      try super.nextToken() finally c.end(f, this)

    override def handleNewLine(lastToken: Int): Unit =
      capture.captureNext(this, "before-handleNewLine")
      capture.around("handleNewLine", this)(super.handleNewLine(lastToken))

    override def postProcessToken(lastToken: Int, lastName: SimpleName | Null): Unit =
      capture.captureNext(this, "before-postProcessToken")
      capture.around("postProcessToken", this)(super.postProcessToken(lastToken, lastName))

    override def peekAhead(): Unit =
      val c = capture
      val f = c.begin("peekAhead", this)
      try
        super.peekAhead()
        c.capture(f, this, "after-peekAhead")
      finally c.end(f, this)

    override def reset(): Unit = capture.around("reset", this)(super.reset())
    override def insert(token: Int, offset: Int): Unit =
      capture.around("insert", this)(super.insert(token, offset))
    override def observeColonEOL(inTemplate: Boolean): Unit =
      capture.around("observeColonEOL", this)(super.observeColonEOL(inTemplate))
    override def observeArrowIndented(): Unit =
      capture.around("observeArrowIndented", this)(super.observeArrowIndented())
    override def observeIndented(): Unit = capture.around("observeIndented", this)(super.observeIndented())
    override def observeOutdented(): Unit = capture.around("observeOutdented", this)(super.observeOutdented())
    override def closeIndented(): Unit = capture.around("closeIndented", this)(super.closeIndented())
    override def resume(previous: TokenData): Unit = capture.around("resume", this)(super.resume(previous))
    override protected def isEndMarker: Boolean =
      val result = super.isEndMarker
      capture.event("isEndMarker", "result", this, bool(result))
      result

  // -1 marks the interior of a UTF-16 surrogate pair: it is not a UTF-8 byte
  // boundary. CR/LF are not normalized. Actual native-offset fixtures are still
  // required; this mapping itself does not establish scanner range semantics.
  private def byteBoundaries(s: String): Seq[String] =
    val out = Array.fill(s.length + 1)(-1)
    var i = 0
    var bytes = 0
    out(0) = 0
    while i < s.length do
      val cp = s.codePointAt(i)
      i += Character.charCount(cp)
      bytes += (if cp <= 0x7f then 1 else if cp <= 0x7ff then 2 else if cp <= 0xffff then 3 else 4)
      out(i) = bytes
    out.iterator.map(_.toString).toSeq

  private case class ParseResult(transport: String, clean: Boolean,
      graphClean: Boolean, endedAtEOF: Boolean, comments: List[Comment])

  private def parse(path: Path, text: String, setup: Context, observation: Option[Capture]): ParseResult =
    val unit = CompilationUnit(path.toString, text)
    val reporter = new CaptureReporter
    given Context = setup.fresh.setCompilationUnit(unit).setReporter(reporter)
    require(java.util.Arrays.equals(unit.source.content, text.toCharArray), "virtual source changed decoded input")
    var parser: Option[Parser] = None
    var graph: Option[Graph] = None
    var root: Option[Int] = None
    var failure: Option[String] = None
    try
      val p = observation match
        case None => new Parser(unit.source)
        case Some(c) =>
          require(activeCapture.get() == null, "nested capture session")
          activeCapture.set(c)
          val observedScanner = new ObservedScanner(unit.source)
          c.event("constructor", "initialized", observedScanner)
          // The superclass constructs an EOF-only discarded scanner. Exact
          // Parser construction has no eager read of the overridden in val.
          new Parser(unit.source, limit = 0):
            override val in: Scanner = observedScanner
      parser = Some(p)
      val tree = p.parse()
      val g = new Graph(unit.source)
      root = Some(g.node(tree))
      graph = Some(g)
    catch
      case NonFatal(e) =>
        failure = Some(obj("class" -> quote(e.getClass.getName),
          "message" -> quote(Option(e.getMessage).getOrElse(""))))
    finally
      if observation.nonEmpty then activeCapture.remove()
    val comments = parser.map(_.in.comments).getOrElse(Nil)
    val nativeComments = comments.map(c => obj("span" -> span(c.span),
      "native_raw" -> quote(c.raw), "doc_comment" -> bool(c.isDocComment)))
    val graphClean = graph.exists(_.problems.isEmpty)
    val endedAtEOF = parser.exists(_.in.token == EOF)
    val transport = obj("parse_has_errors" -> bool(reporter.hasErrors),
      "failure" -> failure.getOrElse("null"),
      "incoming_diagnostics" -> arr(reporter.incoming.map(diagnostic)),
      "buffered_diagnostics" -> arr(reporter.pendingMessages.map(diagnostic)),
      "unreported_warning_counts" -> obj(reporter.unreportedWarnings.toSeq.sortBy(_._1).map((k, v) => k -> v.toString)*),
      "root" -> root.map(_.toString).getOrElse("null"),
      "sources" -> arr(graph.toList.flatMap(_.sourceRecords)),
      "nodes" -> arr(graph.toList.flatMap(_.nodes)),
      "structural_edges" -> arr(graph.toList.flatMap(_.edges)),
      "graph_problems" -> arr(graph.toList.flatMap(_.problems)),
      "parser_scanner_comments" -> arr(nativeComments),
      "final_scanner_state" -> parser.map(p => scannerState(p.in)).getOrElse("null"))
    ParseResult(transport, !reporter.hasErrors && failure.isEmpty, graphClean, endedAtEOF, comments)

  private def read(path: Path, stockSetup: Context, observedSetup: Context): String =
    val bytes = Files.readAllBytes(path)
    val digest = MessageDigest.getInstance("SHA-256").digest(bytes).map(b => f"${b & 0xff}%02x").mkString
    val text = StandardCharsets.UTF_8.newDecoder()
      .onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
      .decode(ByteBuffer.wrap(bytes)).toString
    val stock = parse(path, text, stockSetup, None)
    val capture = new Capture(text)
    val observed = parse(path, text, observedSetup, Some(capture))
    // Both contexts process identical inputs in identical order. Retain both
    // complete transports; do not normalize away unexpected differences.
    val parity = stock.transport == observed.transport
    val (coverage, complete) = capture.finish(observed.comments, stock.clean && observed.clean,
      parity, stock.graphClean && observed.graphClean, observed.endedAtEOF)
    obj("schema" -> quote("scala310-parser-token-capture-candidate-v1"),
      "expected_compiler_source_commit" -> quote(expectedCommit),
      "source_path" -> quote(path.toString), "source_sha256" -> quote(digest),
      "source_byte_count" -> bytes.length.toString,
      "source_bytes_base64" -> quote(Base64.getEncoder.encodeToString(bytes)),
      "decoded_text" -> quote(text), "utf16_length" -> text.length.toString,
      "utf16_to_utf8_byte_boundaries" -> arr(byteBoundaries(text)),
      "offset_unit" -> quote("UTF-16 code units"),
      "stock_parser" -> stock.transport, "observed_parser" -> observed.transport,
      "stock_parser_parity" -> bool(parity), "token_capture" -> coverage,
      "candidate_coverage_complete" -> bool(complete),
      "complete_token_coverage_qualified" -> "false", "native_fixture_transport_verified" -> "false",
      "canonical_loc" -> "null", "formatted_loc" -> "null", "chart_admission" -> "false")

  private def setup(classpath: String, output: Path, label: String): Context =
    val base = new ContextBase
    val context = base.initialCtx.fresh
    context.setSetting(context.settings.classpath, classpath)
    context.setSetting(context.settings.sourcepath, "")
    context.setSetting(context.settings.source, "3.10")
    context.setSetting(context.settings.encoding, "UTF-8")
    context.setSetting(context.settings.preview, false)
    context.setSetting(context.settings.experimental, false)
    context.setSetting(context.settings.language, Nil)
    context.setSetting(context.settings.rewrite, false)
    context.setSetting(context.settings.silentWarnings, false)
    context.setSetting(context.settings.Wconf, Nil)
    context.setSetting(context.settings.XdropComments, false)
    context.setSetting(context.settings.YmagicOffsetHeader, "")
    val reporter = new CaptureReporter
    context.setReporter(reporter)
    var failure: Option[Throwable] = None
    try base.initialize()(using context)
    catch case NonFatal(e) => failure = Some(e)
    val record = obj("schema" -> quote("scala310-reader-initialization-v1"),
      "expected_compiler_source_commit" -> quote(expectedCommit),
      "dependency_classpath" -> quote(classpath), "source_version" -> quote("3.10"),
      "mode" -> quote(label), "incoming_diagnostics" -> arr(reporter.incoming.map(diagnostic)),
      "failure" -> failure.map(e => obj("class" -> quote(e.getClass.getName),
        "message" -> quote(Option(e.getMessage).getOrElse("")))).getOrElse("null"))
    Files.writeString(output.resolve("initialization-" + label + ".json"), record + "\n", StandardCharsets.UTF_8,
      StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
    failure.foreach(e => throw e)
    require(reporter.incoming.isEmpty, "compiler initialization produced diagnostics; see initialization artifact")
    context

  // Future supervised invocation: SourceReader <approved dependency classpath>
  // <fresh output directory> <source.scala>... . Each source is parsed twice;
  // no subject is compiled, evaluated or run by this reader's entry point.
  def main(args: Array[String]): Unit =
    require(args.length >= 3, "expected dependency classpath, fresh output directory, and source paths")
    val inputs = args.drop(2).map(p => Path.of(p).toAbsolutePath.normalize())
    require(inputs.distinct.length == inputs.length, "duplicate source path")
    require(inputs.forall(p => Files.isRegularFile(p)), "input is not a regular source file")
    val output = Path.of(args(1)).toAbsolutePath.normalize()
    require(!Files.exists(output), "output directory must be fresh")
    Files.createDirectory(output)
    val stockSetup = setup(args(0), output, "stock")
    val observedSetup = setup(args(0), output, "observed")
    inputs.zipWithIndex.foreach { (path, index) =>
      val record = read(path, stockSetup, observedSetup)
      Files.writeString(output.resolve(f"$index%04d.json"), record + "\n", StandardCharsets.UTF_8,
        StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
    }
