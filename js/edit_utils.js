//
// edit_utils.js  -- Some utilities while editing text
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


var toggleMonospace = function(checked, elementId) {
    e = document.getElementById(elementId);
    if (checked) {
        e.style.fontFamily = "Consolas,Monaco,Lucida Console,Liberation Mono,DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace";
    } else {
        e.style.fontFamily = "";
    }
};
