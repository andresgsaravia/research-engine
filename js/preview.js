//
// preview.js  -- Previews markdown and LaTeX using and Mathjax
//
// we assume Mathjax.js is present

var Preview = function (sourceId, destId) {
    MathJax.InputJax.TeX.resetEquationNumbers();
    inputText = document.getElementById(sourceId).value;
    $.post("/_preview",
	   {content : inputText},
	   function (data, textStatus) {
	       document.getElementById(destId).innerHTML = data;
	       MathJax.Hub.Queue(["Typeset", MathJax.Hub, destId]);
	   });
};
