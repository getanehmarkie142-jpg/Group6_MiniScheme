; Fibonacci, higher-order map, and list length
(define (fib n)
  (if (< n 2)
      n
      (+ (fib (- n 1)) (fib (- n 2)))))

(define (square x) (* x x))

(print (fib 10))
(print (map square '(1 2 3 4)))
(print (length '(10 20 30 40)))
