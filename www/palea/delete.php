<?php

$session = $_REQUEST['se'];

if ( $db = new PDO("sqlite:../../var/palea.db")){


	printf("<html><head>");
	printf("<link href=\"style.css\" rel=\"stylesheet\" type=\"text/css\">");
	printf(" <META http-equiv=\"refresh\" content=\"1;URL=index.php\"> ");
	printf("<title>Deleting session %d</title></head>", $session);
	printf("<body><table width=100%%><tr><td class=\"invisible\"><a href=\"index.php\">[home]</a><br><h1>Deleting sesion %s.....</h1></td>", $session);
	printf("<td class=\"invisible\" align=\"right\"><img src=\"logo.jpg\"></td></tr></table>");

// Einde kop begin executing stuff

	
	$resultnum = $db->exec("DELETE FROM catch WHERE session = $session");
	//print_r($db->errorinfo());
	printf("%s lines deleted from database.",$resultnum);
	printf("</body></html>");

}
?>
