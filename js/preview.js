//
// preview.js  -- Previews markdown and LaTeX
//
// we assume Mathjax.js is present

var timer;

var Preview = function(sourceId, destId, wiki_p_id) {
    clearTimeout(timer);
    timer=setTimeout(function () 
		     {
			 MathJax.InputJax.TeX.resetEquationNumbers();
			 inputText = document.getElementById(sourceId).value;
			 $.post("/_preview",
				{content : inputText,
				 wiki_p_id : wiki_p_id},
				function (data, textStatus) {
				    document.getElementById(destId).innerHTML = data;
				    MathJax.Hub.Queue(["Typeset", MathJax.Hub, destId]);
				});
		     },
		     2000);
};
