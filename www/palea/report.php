<?php

$session = $_REQUEST['se'];

if ( $db = new PDO("sqlite:../../var/palea.db")){


	printf("<html><head><link href=\"style.css\" rel=\"stylesheet\" type=\"text/css\"><title>Results for session %d</title></head>", $session);
	printf("<body><table width=100%%><tr><td class=\"invisible\"><a href=\"index.php\">[home]</a><br><h1>Results for sesion %s</h1></td>", $session);
	printf("<td class=\"invisible\" align=\"right\"><img src=\"logo.jpg\"></td></tr></table>");

// End header section, start of tabular data)

	printf("<table><tr valign=\"TOP\"><td>");
	
	$resultset = $db->query("SELECT * FROM catch WHERE session = $session");
	printf("<table><tr><td class=\"invisible\" colspan=3><h2>All results </h2></td></tr>", $session);
	printf("<tr><td class=\"head\">Row id</td><td class=\"head\">Network station</td><td class=\"head\">Discovered gateway</td><td class=\"head\">Type</td></tr>");
	while($result = $resultset->fetch()){
		printf("<tr><td> %s </td><td>  %s </td><td> %s </td><td> %s </td></tr>", $result['uniqueId'], $result['victim'], $result['gateway'], $result['type'] );
	}
	printf("</table>");
	
	printf("</td><td>");

	$resultset = $db->query("SELECT gateway, count(*) as count FROM catch WHERE session = $session GROUP BY gateway ORDER BY count DESC;");
	printf("<table><tr><td class=\"invisible\" colspan=3><h2>Most found gateways</h2></td></tr>");
	printf("<tr><td class=\"head\">Result #</td><td class=\"head\">Gateway</td><td class=\"head\"># occurences</td></tr>");
	$cnt = 1;
	while($result = $resultset->fetch()){
		printf("<tr><td> %d </td><td> %s </td><td> %s </td></tr>", $cnt++ , $result['gateway'], $result['count']);
	}
	printf("</table></body></html>");

	printf("</td</tr></table>");
}
?>
