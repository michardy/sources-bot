console.log('running');
var box = document.getElementById('searchbox');
console.log(box);
box.type = "url";
box.placeholder = "https://...";
console.log('ran');

function update_search(button) {
	console.log('changing');
	if (button.value == "url") {
		if (button.checked) {
			var type = "url";
			var hint = "https://...";
		} else {
			var type = "text";
			var hint = "Article title";
		}
	} else {
		if (button.checked) {
			var type = "text";
			var hint = "Article title";
		} else {
			var type = "url";
			var hint = "https://...";
		}
	}
	box.type = type;
	box.placeholder = hint;
}
