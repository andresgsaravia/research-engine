//
// preview.js  -- Previews markdown and LaTeX using and Mathjax
//
// we assume Mathjax.js is present

var timer;

var Preview = function(sourceId, destId) {
    clearTimeout(timer);
    timer=setTimeout(function () 
		     {
			 MathJax.InputJax.TeX.resetEquationNumbers();
			 inputText = document.getElementById(sourceId).value;
			 $.post("/_preview",
				{content : inputText},
				function (data, textStatus) {
				    document.getElementById(destId).innerHTML = data;
				    MathJax.Hub.Queue(["Typeset", MathJax.Hub, destId]);
				});
		     },
		     2000);
};
