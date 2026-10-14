// Source-only draft for scala/scala3 25c18aaa21b6be202945e024cd5180d9d62d650f.
// Not compiled or run. This transports parser evidence; it does not count LOC.
package benchmark.scala310

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
import dotty.tools.dotc.core.Names.Name
import dotty.tools.dotc.parsing.Parsers.Parser
import dotty.tools.dotc.reporting.{Diagnostic, StoreReporter}
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

  private def read(path: Path, setup: Context): String =
    val bytes = Files.readAllBytes(path)
    val digest = MessageDigest.getInstance("SHA-256").digest(bytes).map(b => f"${b & 0xff}%02x").mkString
    val text = StandardCharsets.UTF_8.newDecoder()
      .onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
      .decode(ByteBuffer.wrap(bytes)).toString
    val unit = CompilationUnit(path.toString, text)
    val reporter = new CaptureReporter
    given Context = setup.fresh.setCompilationUnit(unit).setReporter(reporter)
    require(java.util.Arrays.equals(unit.source.content, text.toCharArray), "virtual source changed decoded input")
    val parser = new Parser(unit.source)
    val tree = parser.parse()
    val graph = new Graph(unit.source)
    val root = graph.node(tree)
    val comments = parser.in.comments.map { c =>
      obj("span" -> span(c.span), "native_raw" -> quote(c.raw), "doc_comment" -> bool(c.isDocComment))
    }
    val buffered = reporter.pendingMessages
    obj("schema" -> quote("scala310-untyped-source-transport-v1"),
      "expected_compiler_source_commit" -> quote(expectedCommit),
      "source_path" -> quote(path.toString), "source_sha256" -> quote(digest),
      "source_byte_count" -> bytes.length.toString,
      "source_bytes_base64" -> quote(Base64.getEncoder.encodeToString(bytes)),
      "decoded_text" -> quote(text), "utf16_length" -> text.length.toString,
      "utf16_to_utf8_byte_boundaries" -> arr(byteBoundaries(text)),
      "offset_unit_source_review" -> quote("UTF-16 code units; native fixtures pending"),
      "parse_has_errors" -> bool(reporter.hasErrors),
      "incoming_diagnostics" -> arr(reporter.incoming.map(diagnostic)),
      "buffered_diagnostics" -> arr(buffered.map(diagnostic)),
      "unreported_warning_counts" -> obj(reporter.unreportedWarnings.toSeq.sortBy(_._1).map((k, v) => k -> v.toString)*),
      "root" -> root.toString, "sources" -> arr(graph.sourceRecords),
      "nodes" -> arr(graph.nodes), "structural_edges" -> arr(graph.edges),
      "graph_problems" -> arr(graph.problems), "parser_scanner_comments" -> arr(comments),
      "final_scanner_state" -> obj("token" -> parser.in.token.toString,
        "offset" -> parser.in.offset.toString, "previous_token_end" -> parser.in.lastOffset.toString),
      "complete_token_coverage" -> "false", "native_fixture_transport_verified" -> "false",
      "canonical_loc" -> "null", "formatted_loc" -> "null", "chart_admission" -> "false")

  // Future supervised invocation: SourceReader <approved dependency classpath>
  // <fresh output directory> <source.scala>... . The dependency classpath must
  // exclude benchmark classes. This file supplies no download or launch logic.
  def main(args: Array[String]): Unit =
    require(args.length >= 3, "expected dependency classpath, fresh output directory, and source paths")
    val inputs = args.drop(2).map(p => Path.of(p).toAbsolutePath.normalize())
    require(inputs.distinct.length == inputs.length, "duplicate source path")
    require(inputs.forall(p => Files.isRegularFile(p)), "input is not a regular source file")
    val output = Path.of(args(1)).toAbsolutePath.normalize()
    require(!Files.exists(output), "output directory must be fresh")
    val base = new ContextBase
    val setup = base.initialCtx.fresh
    setup.setSetting(setup.settings.classpath, args(0))
    setup.setSetting(setup.settings.sourcepath, "")
    setup.setSetting(setup.settings.source, "3.10")
    setup.setSetting(setup.settings.encoding, "UTF-8")
    setup.setSetting(setup.settings.preview, false)
    setup.setSetting(setup.settings.experimental, false)
    setup.setSetting(setup.settings.language, Nil)
    setup.setSetting(setup.settings.rewrite, false)
    setup.setSetting(setup.settings.silentWarnings, false)
    setup.setSetting(setup.settings.Wconf, Nil)
    setup.setSetting(setup.settings.XdropComments, false)
    setup.setSetting(setup.settings.YmagicOffsetHeader, "")
    val initializationReporter = new CaptureReporter
    setup.setReporter(initializationReporter)
    Files.createDirectory(output)
    var initializationFailure: Option[Throwable] = None
    try base.initialize()(using setup)
    catch case NonFatal(e) => initializationFailure = Some(e)
    val initialization = obj("schema" -> quote("scala310-reader-initialization-v1"),
      "expected_compiler_source_commit" -> quote(expectedCommit),
      "dependency_classpath" -> quote(args(0)), "source_version" -> quote("3.10"),
      "incoming_diagnostics" -> arr(initializationReporter.incoming.map(diagnostic)),
      "failure" -> initializationFailure.map(e => obj("class" -> quote(e.getClass.getName),
        "message" -> quote(Option(e.getMessage).getOrElse("")))).getOrElse("null"))
    Files.writeString(output.resolve("initialization.json"), initialization + "\n", StandardCharsets.UTF_8,
      StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
    initializationFailure.foreach(e => throw e)
    require(initializationReporter.incoming.isEmpty, "compiler initialization produced diagnostics; see initialization.json")
    inputs.zipWithIndex.foreach { (path, index) =>
      val record = read(path, setup)
      Files.writeString(output.resolve(f"$index%04d.json"), record + "\n", StandardCharsets.UTF_8,
        StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
    }
