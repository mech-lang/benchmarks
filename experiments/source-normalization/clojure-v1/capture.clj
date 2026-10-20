;; Read-only capture harness. This file is trusted tooling; retained source is
;; supplied only to tools.reader/read, never load/eval/require/macroexpand.
(require '[clojure.edn :as edn]
         '[clojure.string :as string]
         '[clojure.tools.reader :as reader]
         '[clojure.tools.reader.reader-types :as types])
(import '[java.nio.charset StandardCharsets]
        '[java.security MessageDigest])

(defn digest [^String value]
  (let [bytes (.digest (MessageDigest/getInstance "SHA-256") (.getBytes value StandardCharsets/UTF_8))]
    (apply str (map #(format "%02x" (bit-and (int %) 255)) bytes))))

(defn json-string [value]
  (str "\"" (apply str (map (fn [c]
    (case c \" "\\\"" \\ "\\\\" \newline "\\n" \return "\\r" \tab "\\t"
      (if (< (int c) 32) (format "\\u%04x" (int c)) (str c)))) (str value))) "\""))

(declare json-value)
(defn json-value [value]
  (cond (nil? value) "null"
        (true? value) "true"
        (false? value) "false"
        (number? value) (str value)
        (string? value) (json-string value)
        (keyword? value) (json-string (name value))
        (map? value) (str "{" (clojure.string/join "," (map (fn [[k v]] (str (json-string (if (keyword? k) (name k) k)) ":" (json-value v))) (sort-by (comp str key) value))) "}")
        (sequential? value) (str "[" (clojure.string/join "," (map json-value value)) "]")
        :else (throw (IllegalArgumentException. "Unexpected capture JSON value"))))

(defn line-starts [^String text]
  (loop [i 0 result [0]]
    (if (= i (.length text)) result
      (let [c (.charAt text i)]
        (cond (= c \return) (let [next (if (and (< (inc i) (.length text)) (= (.charAt text (inc i)) \newline)) (+ i 2) (inc i))]
                             (recur next (conj result next)))
              (= c \newline) (recur (inc i) (conj result (inc i)))
              :else (recur (inc i) result))))))

(def ^:dynamic *frames* [])
(def core-macros (vec (sort (map (comp str key) (filter (fn [[_ v]] (:macro (meta v))) (ns-publics 'clojure.core))))))
(def core-functions (vec (sort (map (comp str key) (filter (fn [[_ v]] (and (not (:macro (meta v))) (fn? @v))) (ns-publics 'clojure.core))))))
(defn kind [value eof delimiter]
  (cond (identical? value eof) "eof"
        (identical? value delimiter) "delimiter"
        (nil? value) "nil"
        (symbol? value) "symbol"
        (keyword? value) "keyword"
        (string? value) "string"
        (char? value) "character"
        (number? value) "number"
        (boolean? value) "boolean"
        (vector? value) "vector"
        (map? value) "map"
        (set? value) "set"
        (seq? value) "list"
        (instance? java.util.regex.Pattern value) "regex"
        :else (throw (IllegalArgumentException. (str "Unknown native reader value class " (class value))))))

(defn capture [id text expected-sha]
  (let [rdr (types/source-logging-push-back-reader text 4 id)
        starts (line-starts text) events (atom []) serial (atom 0)
        read-var (ns-resolve 'clojure.tools.reader 'read*) original @read-var
        delimiter @(ns-resolve 'clojure.tools.reader 'READ_FINISHED) eof (Object.)
        position (fn [] (+ (nth starts (dec (types/get-line-number rdr))) (dec (types/get-column-number rdr))))
        wrapped (fn [& args]
                  (let [event-id (swap! serial inc) parent (peek *frames*) begin (position)]
                    (binding [*frames* (conj *frames* event-id)]
                      (let [value (apply original args)
                            event {:id event-id :parent parent :start_utf16 begin :end_utf16 (position)
                                   :kind (kind value eof delimiter)}]
                        (swap! events conj event)
                        value))))]
    (when-not (= expected-sha (digest text)) (throw (IllegalArgumentException. "Input hash differs")))
    (try
      (binding [*read-eval* false *data-readers* {} *default-data-reader-fn* nil
                reader/*read-eval* false reader/*data-readers* {} reader/*default-data-reader-fn* nil
                reader/*alias-map* {}]
        (with-redefs-fn {read-var wrapped #'reader/default-data-readers {}}
          (fn []
            (loop [forms 0]
              (let [value (reader/read {:eof eof} rdr)]
                (if (identical? value eof)
                  {:accepted true :source_sha256 expected-sha :top_level_forms forms
                   :read_eval false :source_evaluated false :macroexpanded false :custom_data_readers false
                   :core_macro_names core-macros :core_function_names core-functions :events (vec (sort-by :id @events))}
                  (recur (inc forms))))))))
      (catch Exception error
        {:accepted false :source_sha256 expected-sha :error (.getMessage error)
         :read_eval false :source_evaluated false :macroexpanded false :custom_data_readers false
         :core_macro_names core-macros :core_function_names core-functions :events (vec (sort-by :id @events))}))))

(let [jobs (edn/read-string {:readers {} :default (fn [& _] (throw (IllegalArgumentException. "Tagged manifest data forbidden")))} (slurp (first *command-line-args*)))]
  (when-not (= (clojure-version) "1.12.6") (throw (IllegalStateException. "Wrong pinned Clojure version")))
  (println (json-value {:schema "clojure-native-reader-capture.v1" :clojure_version (clojure-version)
    :java_runtime_version (System/getProperty "java.runtime.version") :tools_reader_version "1.6.0"
    :jobs (into {} (map (fn [[id text digest]] [id (capture id text digest)]) jobs))})))
