(define (square x) (* x x))
(print (square 5))
(print ((lambda (x y) (+ x y)) 3 4))

(define (make-adder n) (lambda (x) (+ x n)))
(define add5 (make-adder 5))
(print (add5 10))

(define (sum lst)
  (if (null? lst)
      0
      (+ (car lst) (sum (cdr lst)))))
(print (sum '(1 2 3 4 5)))
(print (cons 1 '(2 3)))
(let ((a 2) (b 3)) (print (* a b)))
