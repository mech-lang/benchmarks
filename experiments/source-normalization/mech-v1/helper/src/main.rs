use mech_syntax::document::{DocumentId,Revision,TextSnapshot,ParseConfig,parse_canonical_document,SyntaxNode,SyntaxElement};
use serde_json::{json,Value};
fn node(n:SyntaxNode)->Value {
 let children:Vec<Value>=n.children_with_tokens().into_iter().map(|e|match e {
  SyntaxElement::Node(n)=>node(n),
  SyntaxElement::Token(t)=>json!({"token":true,"kind":format!("{:?}",t.kind()),"start":t.range().start.0,"end":t.range().end.0,"text":t.text().unwrap()})
 }).collect();
 json!({"token":false,"kind":format!("{:?}",n.kind()),"start":n.range().start.0,"end":n.range().end.0,"children":children})
}
fn main(){
 let path=std::env::args().nth(1).expect("source path");
 let text=std::fs::read_to_string(&path).unwrap();
 let parsed=parse_canonical_document(TextSnapshot::new(DocumentId(1),Revision(0),text.clone()).unwrap(),ParseConfig::default());
 let syntax=parsed.syntax();
 assert_eq!(syntax.text().unwrap(),text);
 println!("{}",json!({"schema":"mech-native-cst-capture.v1","path":path,"source":text,"diagnostics":format!("{:?}",parsed.diagnostics),"syntax":node(syntax)}));
}
