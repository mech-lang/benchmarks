def classify(x: Int): Int = x match { case 0 => 1; case n if n > 0 => n; case _ => -1 }
