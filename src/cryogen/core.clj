(ns cryogen.core
  (:require [cryogen.compile]
            ;[cryogen-core.compiler :refer [compile-assets-timed]]
            [cryogen-core.plugins :refer [load-plugins]]))

(defn -main []
  (load-plugins)
  ;(compile-assets-timed)
  (cryogen.compile/compile-site)  
  (System/exit 0))
