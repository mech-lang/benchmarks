# Bounded permutation matrices and indexed prefix reversals; no native kernel.
run <- function(n) {
  factorials <- c(1,cumprod(seq_len(n)))
  total <- factorials[n+1L]
  workers <- min(8L,total)
  ranges <- floor(seq.int(0L,workers)*total/workers)
  reversals <- vapply(seq_len(n), function(width) c(rev(seq_len(width)), if (width < n) seq.int(width+1L,n) else integer()), integer(n))
  gathers <- matrix(as.integer(rep(reversals,8192L)+rep(seq.int(0L,8191L)*n,each=n*n)),n)
  task <- function(worker) {
    checksum <- 0
    maximum <- 0L
    for (start in seq.int(ranges[worker],ranges[worker+1L]-1L,by=8192L)) {
      ranks <- seq.int(start,min(start+8191L,ranges[worker+1L]-1L))
      remainder <- ranks
      permutation <- matrix(rep(seq_len(n),length(ranks)),n)
      if (n >= 2L) for (i in seq.int(n,2L,by=-1L)) {
        digit <- remainder %/% factorials[i]
        remainder <- remainder %% factorials[i]
        gather <- (rep(seq_len(i)-1L,length(ranks))+rep(digit,each=i)) %% i+1L+rep(seq_along(ranks)-1L,each=i)*n
        permutation[seq_len(i),] <- permutation[gather]
      }
      flips <- integer(length(ranks))
      active <- which(permutation[1L,] != 1L)
      while (length(active)) {
        gather <- gathers[,(active-1L)*n+permutation[1L,active],drop=FALSE]
        permutation[,active] <- permutation[gather]
        flips[active] <- flips[active]+1L
        active <- active[permutation[1L,active] != 1L]
      }
      checksum <- checksum+sum(flips*ifelse(ranks %% 2L,-1L,1L))
      maximum <- max(maximum,flips)
    }
    c(checksum,maximum)
  }
  result <- parallel::mclapply(seq_len(workers),task,mc.cores=workers,mc.preschedule=TRUE)
  cat(sprintf("%.0f\nPfannkuchen(%d) = %.0f\n",sum(vapply(result,`[`,0.0,1L)),n,max(vapply(result,`[`,0.0,2L))))
}
run(as.integer(commandArgs(TRUE)[1L]))
