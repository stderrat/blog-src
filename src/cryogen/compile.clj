(ns cryogen.compile
  (:require [cryogen-core.compiler :refer [compile-assets-timed]]
            [net.cgrand.enlive-html :as enlive])
  (:import (java.io StringReader)))

;;---------------------------------------------------------- custom URI override

(defn slug->uri [{:keys [slug] :as article} _]
  (cond-> article
          slug (assoc :uri (str "/" slug "/"))))

;;--------------------------------------------------------------------- compile

(defn compile-site []
  (compile-assets-timed
    {:update-article-fn
     (fn update-article [{:keys [slug] :as article} config]
       (if slug
         (assoc article :uri (str "/" slug "/"))
         article))

     :extend-params-fn
     (fn extend-params [params site-data]
       (let [tag-count (->> (:posts-by-tag site-data)
                            (map (fn [[k v]] [k (count v)]))
                            (into {}))]
         (update
           params :tags
           #(map (fn [t] (assoc t
                           :count (tag-count (:name t))))
                 %))))}))